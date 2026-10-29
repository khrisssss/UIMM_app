import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
from app.models.company import Company
from app.models.company_profile_question import CompanyProfileQuestion
from app.models.company_profile_answer import CompanyProfileAnswer
from app.models.answer import Answer
from app.models.question import Question
from app.models.score import Score
from app.models.swot import SWOT
from app.models.reports import Report
from app.models.financial_year import FinancialYear
from app.services.questionnaire_import_service import import_questionnaire
from app.services.public_company_import_service import import_public_companies, PROFILE_QUESTION
from app.services.ml_demo_data_service import seed_demo_data
from app.services.complete_case_service import create_complete_case
from app.services.generated_data_cleanup_service import cleanup_generated_data


def populate(db):
    import_questionnaire(db, apply=True, activate=True)
    import_public_companies(db, apply=True)
    seed_demo_data(db, apply=True, per_class=4)
    create_complete_case(db, apply=True)
    real = Company(name='Original customer', general_comment='Original consultant notes', general_state='green')
    same_name = Company(name='COMAT', general_comment='Original customer, not imported by the tool')
    db.add_all([real, same_name]); db.flush()
    question = db.query(Question).first()
    db.add_all([Answer(company_id=real.id, question_id=question.id, score_value=3), Score(company_id=real.id, axis_id=question.axis_id), SWOT(company_id=real.id, strengths='Original finding'), Report(company_id=real.id, title='Original report'), FinancialYear(company_id=real.id, year=2026, kind='actual', revenue=100)])
    generated = db.query(Company).filter_by(is_synthetic=True).first()
    db.add_all([SWOT(company_id=generated.id, strengths='Generated'), Report(company_id=generated.id, title='Generated report'), FinancialYear(company_id=generated.id, year=2026, kind='actual', revenue=1)])
    db.commit()
    return real.id, same_name.id


def test_preview_does_not_remove_or_write_backup(configured_db, tmp_path):
    real_id, _ = populate(configured_db)
    result = cleanup_generated_data(configured_db, backup_directory=tmp_path)
    assert result['company_count'] == 33
    assert result['public_research_questions'] == 1
    assert configured_db.query(Company).count() == 35
    assert configured_db.get(Company, real_id).general_comment == 'Original consultant notes'
    assert not list(tmp_path.iterdir())


def test_cleanup_removes_generated_data_and_question_preserves_real_companies(configured_db, tmp_path):
    db = configured_db
    real_id, original_comat_id = populate(db)
    result = cleanup_generated_data(db, apply=True, backup_directory=tmp_path); db.commit()
    assert result['deleted_companies'] == 33 and result['deleted_profile_questions'] == 1
    assert db.query(Company).count() == 2
    assert db.get(Company, real_id) and db.get(Company, original_comat_id)
    assert db.query(CompanyProfileQuestion).filter_by(question_text=PROFILE_QUESTION).count() == 0
    assert db.query(Answer).count() == db.query(Score).count() == db.query(SWOT).count() == db.query(Report).count() == db.query(FinancialYear).count() == 1
    assert db.query(Answer).one().company_id == real_id
    assert db.query(Report).one().title == 'Original report'
    assert db.query(CompanyProfileQuestion).count() == 20  # Ordinary questionnaires survive.
    backup = json.loads(Path(result['backup']).read_text())
    assert len(backup['tables']['companies']) == 33
    assert backup['tables']['company_profile_questions'][0]['question_text'] == PROFILE_QUESTION
    assert Path(result['backup']).stat().st_mode & 0o777 == 0o600
    repeated = cleanup_generated_data(db, apply=True, backup_directory=tmp_path)
    assert repeated['deleted_companies'] == repeated['deleted_profile_questions'] == 0


def test_backup_failure_prevents_deletion(configured_db, tmp_path):
    populate(configured_db)
    not_a_directory = tmp_path / 'file'
    not_a_directory.write_text('keep')
    with pytest.raises(FileExistsError):
        cleanup_generated_data(configured_db, apply=True, backup_directory=not_a_directory)
    configured_db.rollback()
    assert configured_db.query(Company).count() == 35


def test_cleanup_module_registers_models_without_api_credentials():
    result = subprocess.run([sys.executable, '-c', 'from app.scripts.remove_generated_companies import main; from sqlalchemy.orm import configure_mappers; configure_mappers()'], cwd=Path(__file__).resolve().parents[1], env={**os.environ, 'DATABASE_URL': 'sqlite://'}, text=True, capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr
