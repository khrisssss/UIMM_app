import os
from pathlib import Path
import subprocess
import sys

import pytest
from app.models.answer import Answer
from app.models.axis import Axis
from app.models.company import Company
from app.models.company_axis import CompanyAxis
from app.models.company_profile_answer import CompanyProfileAnswer
from app.models.company_profile_question import CompanyProfileQuestion
from app.models.question import Question
from app.models.score import Score
from app.services.complete_case_service import create_complete_case, load_case
from app.services.questionnaire_import_service import import_questionnaire
from app.services.company_state_ml_service import is_demo_company, training_dataset
from app.services.swot_context import build_swot_context
from app.services.swot_ai_payload import make_swot_ai_payload


def test_complete_case_preview_without_writes(configured_db):
    import_questionnaire(configured_db, apply=True, activate=True); configured_db.commit()
    result = create_complete_case(configured_db)
    assert result['axis_count'] == 6 and result['axis_answers'] > 100
    assert result['profile_answers'] == 20
    assert len(result['scores']) == 6 and not result['created']
    assert configured_db.query(Company).count() == 0
    assert configured_db.query(Answer).count() == 0


def test_full_case_answers_scores_and_swot_evidence(configured_db):
    db = configured_db
    import_questionnaire(db, apply=True, activate=True); db.commit()
    result = create_complete_case(db, apply=True); db.commit()
    company = db.query(Company).one()
    assert result['created'] and company.name == 'Atelier Métal Garonne'
    assert company.is_synthetic and is_demo_company(company)
    assert '[CAS_FICTIF]' in company.general_comment
    assert not company.is_archived and company.has_rse
    assert db.query(CompanyAxis).filter_by(company_id=company.id, is_selected=True).count() == 6
    assert db.query(CompanyProfileAnswer).count() == db.query(CompanyProfileQuestion).filter_by(is_active=True).count()
    answers = db.query(Answer).all()
    assert len(answers) == result['axis_answers']
    assert all(a.answer_text and a.comment and a.score_code is not None for a in answers)
    for score in db.query(Score).all():
        pairs = db.query(Answer, Question).join(Question).filter(Answer.company_id == company.id, Question.axis_id == score.axis_id).all()
        assert score.score_total == sum(a.score_value for a, _ in pairs)
        assert score.score_max == sum(q.max_score for _, q in pairs)
        assert score.score_percentage == round(score.score_total / score.score_max * 100)
        assert score.answered_questions == score.total_questions == len(pairs)
    payload = make_swot_ai_payload(build_swot_context(db, company.id), ())
    assert payload['evidence_basis']['mode'] == 'diagnostic'
    assert len(payload['axis_scores']) == 6
    assert payload['answer_scores'] and payload['company_profile']
    assert 'appel d’offres' in payload['company_context']['general_comment']
    before = len(answers)
    repeated = create_complete_case(db, apply=True)
    assert repeated['existing_company_kept']
    assert db.query(Company).count() == 1 and db.query(Answer).count() == before


def test_synthetic_provenance_survives_rename_and_is_excluded_from_real_training(configured_db):
    db = configured_db
    import_questionnaire(db, apply=True, activate=True)
    create_complete_case(db, apply=True); db.commit()
    company = db.query(Company).one()
    company.name = 'Renamed case'
    company.general_comment = 'Edited notes'
    company.is_archived = True
    db.flush()
    assert is_demo_company(company)
    assert training_dataset(db).empty
    assert len(training_dataset(db, use_demo=True)) == 1


def test_existing_same_name_company_is_preserved(configured_db):
    db = configured_db
    company = Company(name=load_case()['name'], general_comment='Original notes')
    db.add(company); db.commit()
    result = create_complete_case(db, apply=True)
    assert result['existing_company_kept'] and not company.is_synthetic
    assert company.general_comment == 'Original notes'
    assert db.query(Answer).count() == 0


def test_case_requires_questions_before_creating_company(configured_db):
    with pytest.raises(ValueError, match='No active questions'):
        create_complete_case(configured_db, apply=True)
    assert configured_db.query(Company).count() == 0


def test_case_command_registers_orm_relationship_targets_in_fresh_process():
    result = subprocess.run([sys.executable, '-c', 'from app.scripts.create_complete_case_study import main; from sqlalchemy.orm import configure_mappers; configure_mappers()'], cwd=Path(__file__).resolve().parents[1], env={**os.environ, 'DATABASE_URL': 'sqlite://'}, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
