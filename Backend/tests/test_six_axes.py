"""Six-axis regression checks with historical Finance data still present."""
from types import SimpleNamespace

import pytest
from app.models.axis import Axis
from app.models.answer import Answer
from app.models.company import Company
from app.models.company_axis import CompanyAxis
from app.models.company_profile_section import CompanyProfileSection
from app.models.company_profile_question import CompanyProfileQuestion
from app.models.company_profile_answer import CompanyProfileAnswer
from app.models.financial_year import FinancialYear
from app.models.question import Question
from app.models.score import Score
from app.models.swot import SWOT
from app.models.reports import Report
from app.services.diagnostic_scope_service import retire_finance
from app.services.questionnaire_import_service import load_bank
from app.services.report_context import build_report_context
from app.services.swot_context import build_swot_context
from app.services.boost_powerpoint_content_service import get_axis_scores, get_selected_report_axes, get_profile_answers


@pytest.fixture
def historical_company(configured_db):
    db = configured_db
    company = Company(name='Existing customer', company_size='<10', general_state='green', is_archived=True)
    db.add(company); db.flush()
    for axis in db.query(Axis).all():
        question = Question(axis_id=axis.id, question_text=f'Question {axis.name}', max_score=5)
        db.add(question); db.flush()
        db.add(Answer(company_id=company.id, question_id=question.id, score_code='4', score_value=4))
        db.add(Score(company_id=company.id, axis_id=axis.id, score_percentage=80, score_total=4, score_max=5, answered_questions=1, total_questions=1))
        db.add(CompanyAxis(company_id=company.id, axis_id=axis.id, is_selected=True, show_in_portfolio=True))
    for name in ['Finances', 'Informations Générales']:
        section = CompanyProfileSection(name=name, order_index=1)
        db.add(section); db.flush()
        question = CompanyProfileQuestion(section_id=section.id, question_text=f'Profile {name}')
        db.add(question); db.flush()
        db.add(CompanyProfileAnswer(company_id=company.id, question_id=question.id, answer_text='Existing answer'))
    db.add(FinancialYear(company_id=company.id, year=2026, kind='actual', revenue=2400000))
    db.commit()
    return company


def test_retirement_keeps_historical_data_and_is_repeatable(configured_db, historical_company):
    db = configured_db
    counts = {model: db.query(model).count() for model in [Axis, CompanyAxis, Question, Answer, Score, CompanyProfileSection, CompanyProfileQuestion, CompanyProfileAnswer, FinancialYear]}
    for _ in range(2):
        retire_finance(db); db.commit()
    assert counts == {model: db.query(model).count() for model in counts}
    assert [a.name for a in db.query(Axis).filter_by(is_active=True).order_by(Axis.order_index)] == ['Stratégie', 'Performance', 'Marketing', 'RH', 'Digitalisation', 'RSE']
    finance = db.query(Axis).filter_by(name='Finance').one()
    assert not finance.is_active
    assert not db.query(Question).filter_by(axis_id=finance.id).one().is_active
    selection = db.query(CompanyAxis).filter_by(axis_id=finance.id).one()
    assert not selection.is_selected and not selection.show_in_portfolio
    assert not db.query(CompanyProfileSection).filter_by(name='Finances').one().is_active
    assert db.query(FinancialYear).one().revenue == 2400000


def test_contexts_and_powerpoint_omit_retired_axis_and_profile(configured_db, historical_company):
    db = configured_db; company = historical_company
    retire_finance(db); db.commit()
    swot = build_swot_context(db, company.id)
    report = build_report_context(company.id, db)
    assert len(swot['selected_axes']) == len(swot['axis_scores']) == 6
    assert len(report['selected_axes']) == len(report['scores']) == 6
    assert all(q['axis_name'] != 'Finance' for q in swot['diagnostic_answers'])
    assert all(q['axis'] != 'Finance' for q in report['diagnostic_answers'])
    assert [q['section'] for q in report['company_profile']] == ['Informations Générales']
    assert [q['section'] for q in swot['company_profile']] == ['Informations Générales']
    scores = get_axis_scores(db, company.id)
    assert len(scores) == len(get_selected_report_axes(db, company.id, scores)) == 6
    assert len(get_profile_answers(db, company.id)) == 1


def test_company_selection_radar_and_recalculation_exclude_finance(configured_db, historical_company):
    from fastapi import HTTPException
    from app.routers.company_axes import get_company_axes_selection, get_diagnostic_overview, get_company_axis_questions
    from app.routers.scores import get_company_scores, calculate_company_scores, get_archive_average_scores
    from app.routers.company_profile import get_company_profile_questions, admin_get_company_profile_sections, admin_get_company_profile_questions
    db = configured_db; company = historical_company
    retire_finance(db); db.commit()
    user = SimpleNamespace(role='admin')
    finance = db.query(Axis).filter_by(name='Finance').one()
    assert len(get_company_axes_selection(company.id, db, user)) == 6
    assert len(get_diagnostic_overview(company.id, db, user)) == 6
    assert len(get_company_scores(company.id, db, user)) == 6
    assert len(get_archive_average_scores(company.id, db, user)) == 6
    with pytest.raises(HTTPException):
        get_company_axis_questions(company.id, finance.id, db, user)
    assert len(calculate_company_scores(company.id, db, user)) == 6
    assert db.query(Score).filter_by(company_id=company.id, axis_id=finance.id).count() == 1
    assert len(get_company_profile_questions(db, user)) == 1
    assert len(admin_get_company_profile_sections(db, user)) == 1
    assert len(admin_get_company_profile_questions(db, user)) == 1


def test_axis_seed_creates_only_six_axes_on_new_database(db, monkeypatch):
    from sqlalchemy.orm import Session
    from app import seed_axes
    monkeypatch.setattr(seed_axes, 'SessionLocal', lambda: Session(db.bind))
    seed_axes.seed_axes()
    seed_axes.seed_axes()
    assert [a.name for a in db.query(Axis).order_by(Axis.order_index)] == ['Stratégie', 'Performance', 'Marketing', 'RH', 'Digitalisation', 'RSE']
