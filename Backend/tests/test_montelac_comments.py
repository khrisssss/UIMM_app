import pytest
from app.models.answer import Answer
from app.models.company import Company
from app.models.company_profile_answer import CompanyProfileAnswer
from app.models.question import Question
from app.models.score import Score
from app.services.montelac_import_service import install_montelac, load_montelac
from app.services.montelac_comments_service import fill_montelac_comments
from app.services.questionnaire_import_service import import_questionnaire


def install(db):
    import_questionnaire(db, apply=True, activate=True); db.commit()
    result = install_montelac(db); db.commit()
    return result['company_id']


def test_fill_comments_preserves_answers_scores_other_companies_and_repeats_safely(configured_db):
    db = configured_db
    cid = install(db)
    before = [(a.id, a.answer_text, a.score_code, a.score_value) for a in db.query(Answer).order_by(Answer.id)]
    scores = [(s.axis_id, s.score_total, s.score_max, s.score_percentage) for s in db.query(Score).order_by(Score.id)]
    first = db.query(Answer).order_by(Answer.id).first()
    first.comment = 'Commentaire saisi par le consultant.'
    other = Company(name='Other company'); db.add(other); db.flush()
    untouched = Answer(company_id=other.id, question_id=first.question_id, answer_text='Other response')
    db.add(untouched); db.commit()
    result = fill_montelac_comments(db, company_id=cid); db.commit()
    assert result['axis_comments_added'] == 200 and result['axis_comments_preserved'] == 1
    assert result['profile_comments_added'] == 20
    assert result['all_axis_comments_filled'] and result['all_profile_comments_filled']
    assert first.comment == 'Commentaire saisi par le consultant.' and untouched.comment is None
    assert [(a.id, a.answer_text, a.score_code, a.score_value) for a in db.query(Answer).filter_by(company_id=cid).order_by(Answer.id)] == before
    assert [(s.axis_id, s.score_total, s.score_max, s.score_percentage) for s in db.query(Score).order_by(Score.id)] == scores
    repeated = fill_montelac_comments(db, company_id=cid)
    assert repeated['axis_comments_added'] == repeated['profile_comments_added'] == 0
    assert repeated['axis_comments_preserved'] == 201


def test_changed_answer_prevents_all_writes(configured_db):
    db = configured_db
    cid = install(db)
    db.query(Answer).first().answer_text = 'Updated answer from consultant'; db.commit()
    with pytest.raises(ValueError, match='Question or answer changed'):
        fill_montelac_comments(db, company_id=cid)
    db.rollback()
    assert all(a.comment is None for a in db.query(Answer))
    assert all(a.comment is None for a in db.query(CompanyProfileAnswer))


def test_preview_rolls_back_and_company_identity_is_checked(configured_db):
    db = configured_db
    cid = install(db)
    fill_montelac_comments(db, company_id=cid); db.rollback()
    assert all(a.comment is None for a in db.query(Answer))
    db.get(Company, cid).is_synthetic = False; db.commit()
    with pytest.raises(ValueError, match='expected generated'):
        fill_montelac_comments(db, company_id=cid)


def test_every_authored_question_has_a_substantive_comment():
    case = load_montelac()
    for r in case['axis_responses'] + case['profile_responses']:
        assert len(r['comment']) >= 80
        assert r['comment'] != r['answer']


def test_live_label_variants_are_commented(configured_db):
    import json
    from pathlib import Path
    from app.models.axis import Axis
    from app.models.company_profile_section import CompanyProfileSection
    from app.models.company_profile_question import CompanyProfileQuestion
    db = configured_db
    import_questionnaire(db, apply=True, activate=True); db.commit()
    labels = json.loads((Path(__file__).parent/'fixtures'/'montelac_live_questions.json').read_text())
    for item in labels:
        if 'axis' in item:
            axis = db.query(Axis).filter_by(name=item['axis']).one()
            db.add(Question(axis_id=axis.id, question_text=item['question'], max_score=item['maximum'], is_active=True))
        else:
            section = db.query(CompanyProfileSection).filter_by(name=item['section']).one()
            db.add(CompanyProfileQuestion(section_id=section.id, question_text=item['question'], is_active=True))
    db.commit()
    cid = install_montelac(db)['company_id']; db.commit()
    result = fill_montelac_comments(db, company_id=cid); db.commit()
    assert result['axis_comments_added'] == 255 and result['profile_comments_added'] == 22
    assert all(a.comment for a in db.query(Answer))
