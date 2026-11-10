import pytest
from app.models.answer import Answer
from app.models.axis import Axis
from app.models.company import Company
from app.models.company_axis import CompanyAxis
from app.models.company_profile_answer import CompanyProfileAnswer
from app.models.question import Question
from app.models.score import Score
from app.services.montelac_import_service import install_montelac, load_montelac, calculate_axis
from app.services.questionnaire_import_service import import_questionnaire


def test_install_answers_every_question_with_real_score_codes_and_is_repeatable(configured_db):
    db = configured_db
    import_questionnaire(db, apply=True, activate=True); db.commit()
    result = install_montelac(db); db.commit()
    assert result['created'] and result['axis_answers'] == 201 and result['profile_answers'] == 20
    company = db.query(Company).one()
    assert company.name == 'Précision Montelac' and company.company_size == '11-50'
    assert company.is_synthetic and not company.is_archived
    assert db.query(CompanyAxis).filter_by(company_id=company.id, is_selected=True, show_in_portfolio=True).count() == 6
    assert db.query(CompanyProfileAnswer).count() == 20
    assert all(a.answer_text and a.score_code is not None for a in db.query(Answer))
    for saved in db.query(Score):
        axis = db.get(Axis, saved.axis_id)
        assert saved.answered_questions == saved.total_questions
        for key, value in calculate_axis(db, company, axis).items():
            assert getattr(saved, key) == value
    for item in load_montelac()['question_updates']:
        assert db.query(Question).filter_by(question_text=item['question'], is_active=True).count() == 1
    second = install_montelac(db); db.commit()
    assert second['existing_company_kept'] and not second['created']
    assert all(q['action'] == 'kept' for q in second['question_changes'])
    assert db.query(Company).count() == 1 and db.query(Answer).count() == 201


def test_legacy_position_is_renamed_without_losing_answers_and_current_scores_are_updated(configured_db):
    db = configured_db
    import_questionnaire(db, apply=True, activate=True); db.commit()
    update = load_montelac()['question_updates'][0]
    q = db.query(Question).filter_by(question_text=update['question']).one()
    q.question_text = update['aliases'][0]
    axis = db.get(Axis, q.axis_id)
    existing = Company(name='Existing company', company_size='11-50', is_archived=False)
    archived = Company(name='Archived company', company_size='11-50', is_archived=True)
    db.add_all([existing, archived]); db.flush()
    db.add(Answer(company_id=existing.id, question_id=q.id, answer_text='Keep original', score_code='4', score_value=4))
    for c in [existing, archived]:
        db.add(CompanyAxis(company_id=c.id, axis_id=axis.id, is_selected=True))
        db.add(Score(company_id=c.id, axis_id=axis.id, score_total=4, score_max=5, score_percentage=80, answered_questions=1, total_questions=1))
    db.commit()
    result = install_montelac(db); db.commit()
    assert db.get(Question, q.id).question_text == update['question']
    assert db.query(Answer).filter_by(company_id=existing.id).one().answer_text == 'Keep original'
    assert result['current_scores_refreshed'] == 1
    assert db.query(Score).filter_by(company_id=existing.id).one().score_max > 5
    assert db.query(Score).filter_by(company_id=archived.id).one().score_max == 5


def test_unknown_live_question_rolls_back_all_installation_writes(configured_db):
    db = configured_db
    import_questionnaire(db, apply=True, activate=True); db.commit()
    axis = db.query(Axis).filter_by(name='Stratégie').one()
    db.add(Question(axis_id=axis.id, question_text='A new business-specific question', max_score=5, is_active=True))
    db.commit()
    before = db.query(Question).count()
    with pytest.raises(ValueError, match='No specific answer'):
        install_montelac(db)
    db.rollback()
    assert db.query(Question).count() == before
    assert db.query(Company).count() == 0
    assert db.query(Answer).count() == 0


def test_preview_rollback_and_existing_company_protection(configured_db):
    db = configured_db
    import_questionnaire(db, apply=True, activate=True); db.commit()
    assert install_montelac(db)['created']
    db.rollback()
    assert db.query(Company).count() == 0 and db.query(Answer).count() == 0
    kept = Company(name=load_montelac()['name'], general_comment='User content')
    db.add(kept); db.commit()
    result = install_montelac(db); db.commit()
    assert result['existing_company_kept'] and not kept.is_synthetic
    assert kept.general_comment == 'User content' and db.query(Answer).count() == 0


def test_rse_uses_the_number_of_true_statements():
    for response in load_montelac()['axis_responses']:
        if response.get('source_question_id', 0) >= 7001:
            assert response['score'] == sum(line.startswith('Satisfaite :') for line in response['answer'].splitlines())


def test_actual_live_wordings_and_additional_security_questions_are_fully_answered(configured_db):
    import json
    from pathlib import Path
    from app.models.company_profile_section import CompanyProfileSection
    from app.models.company_profile_question import CompanyProfileQuestion
    db = configured_db
    import_questionnaire(db, apply=True, activate=True); db.commit()
    live = json.loads((Path(__file__).parent / 'fixtures' / 'montelac_live_questions.json').read_text())
    for item in live:
        if 'axis' in item:
            axis = db.query(Axis).filter_by(name=item['axis']).one()
            db.add(Question(axis_id=axis.id, question_text=item['question'], max_score=item['maximum'], is_active=True))
        else:
            section = db.query(CompanyProfileSection).filter_by(name=item['section']).one()
            db.add(CompanyProfileQuestion(section_id=section.id, question_text=item['question'], is_active=True))
    strategy = db.query(Axis).filter_by(name='Stratégie').one()
    db.add(Question(axis_id=strategy.id, question_text='Est elle compatible avec les moyen?', max_score=5, is_active=True))
    db.commit()
    result = install_montelac(db); db.commit()
    assert result['axis_answers'] == 256 and result['profile_answers'] == 22
    assert db.query(Answer).count() == 256
    assert all(s.answered_questions == s.total_questions for s in db.query(Score))
    antivirus = db.query(Question).filter_by(question_text='Un antivirus ou EDR administré est-il déployé sur les postes ?').one()
    assert 'antivirus' in db.query(Answer).filter_by(question_id=antivirus.id).one().answer_text
