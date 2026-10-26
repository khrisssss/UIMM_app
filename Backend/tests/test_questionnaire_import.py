import pytest
from app.models.answer import Answer
from app.models.axis import Axis
from app.models.company import Company
from app.models.company_profile_question import CompanyProfileQuestion
from app.models.question import Question
from app.services.questionnaire_import_service import import_questionnaire, load_bank, question_text
from app.scripts.convert_powerapps_questionnaire import convert


def test_bank_keeps_all_powerapps_questions_and_rse_statements():
    bank = load_bank()
    assert len(bank) == 236
    assert len({r['QuestionID'] for r in bank}) == 236
    assert len([r for r in bank if 'Axe' in r]) == 216
    assert len([r for r in bank if 'Section' in r]) == 20
    rse = [r for r in bank if r.get('Axe') == 'RSE']
    assert len(rse) == 25
    assert all(r['Affirmations'].count('•') == 3 for r in rse)
    assert all(question_text(r).startswith(r['Enjeu'] + '\n\n') for r in rse)
    assert not any(r.get('Axe') == 'Finance' for r in bank)


def test_converter_keeps_concatenated_statements_and_escaped_quotes():
    result = convert('''ClearCollect(c, {QuestionID: 7001, Axe: "RSE", Enjeu: "Un \\"enjeu\\"", Ordre: 1, Affirmations: "A" & Char(10) & "B" & Char(10) & "C"})'''.replace('\\"', '""'))
    r = result['questions'][0]
    assert r['Affirmations'] == 'A\nB\nC'
    assert r['Enjeu'] == 'Un "enjeu"'


def test_import_preview_does_not_write(configured_db):
    summary = import_questionnaire(configured_db)
    assert summary['axis_questions_added'] == 216
    assert summary['profile_questions_added'] == 20
    assert configured_db.query(Question).count() == 0
    assert configured_db.query(CompanyProfileQuestion).count() == 0
    assert not configured_db.new


def test_import_is_idempotent_preserves_answers_and_existing_settings(configured_db):
    db = configured_db
    r = next(r for r in load_bank() if r['QuestionID'] == 1001)
    axis = db.query(Axis).filter_by(name='Stratégie').one()
    existing = Question(axis_id=axis.id, question_text=r['Question'], order_index=99, max_score=5, is_active=False)
    company = Company(name='Real customer')
    db.add_all([existing, company]); db.flush()
    answer = Answer(company_id=company.id, question_id=existing.id, score_value=3)
    db.add(answer); db.commit()
    old_id = existing.id
    first = import_questionnaire(db, apply=True, activate=True)
    db.commit()
    assert first['axis_questions_added'] == 215
    assert db.query(Question).count() == 216
    assert db.query(CompanyProfileQuestion).count() == 20
    assert db.query(Answer).one().question_id == old_id
    assert not existing.is_active and existing.order_index == 99
    second = import_questionnaire(db, apply=True, activate=True)
    assert second['axis_questions_added'] == second['profile_questions_added'] == 0
    assert second['existing_questions_kept'] == 236
    rse = db.query(Question).join(Axis).filter(Axis.name == 'RSE').all()
    assert all(q.max_score == 3 and q.question_text.count('•') == 3 for q in rse)
    digital = db.query(Question).join(Axis).filter(Axis.name == 'Digitalisation').all()
    assert all(q.target_less_than_10 and q.target_11_to_50 and q.target_more_than_50 for q in digital)
    assert any(q.category.name == 'Cybersécurité' for q in digital)


def test_new_questions_are_inactive_by_default(configured_db):
    import_questionnaire(configured_db, apply=True)
    assert configured_db.query(Question).filter_by(is_active=True).count() == 0
    assert configured_db.query(CompanyProfileQuestion).filter_by(is_active=True).count() == 0


def test_missing_scales_fail_before_inserting(configured_db):
    from app.models.scoring_scale import ScoringScale
    configured_db.query(ScoringScale).update({'is_active': False})
    with pytest.raises(ValueError, match='scoring scale'):
        import_questionnaire(configured_db, apply=True)
    assert configured_db.query(Question).count() == 0


def test_transaction_rolls_back_on_invalid_later_record(configured_db):
    db = configured_db
    records = load_bank()[:2]
    records = [records[0], records[0]]
    with pytest.raises(ValueError, match='Duplicate question'):
        with db.begin():
            import_questionnaire(db, apply=True, records=records)
    assert db.query(CompanyProfileQuestion).count() == 0
