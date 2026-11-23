"""The six diagnostic axes, and the clean-up of the seventh axis that older databases still contain."""
from types import SimpleNamespace

import pytest
from app.models.answer import Answer
from app.models.axis import Axis
from app.models.axis_question_category import AxisQuestionCategory
from app.models.company import Company
from app.models.company_axis import CompanyAxis
from app.models.company_profile_answer import CompanyProfileAnswer
from app.models.company_profile_question import CompanyProfileQuestion
from app.models.company_profile_section import CompanyProfileSection
from app.models.question import Question
from app.models.score import Score
from app.models.scoring_level import ScoringLevel
from app.models.scoring_scale import ScoringScale
from app.models.swot import SWOT
from app.services.diagnostic_scope_service import delete_finance_axis
from app.services.swot_context import build_swot_context

SIX_AXES = ['Stratégie', 'Performance', 'Marketing', 'RH', 'Digitalisation', 'RSE']


@pytest.fixture
def old_database(configured_db):
    """A database created before the change: a company diagnosed on the six axes plus an old seventh axis."""
    db = configured_db
    old_axis = Axis(name='Finance', order_index=5, is_active=False)
    db.add(old_axis); db.flush()
    company = Company(name='Existing customer', company_size='<10', general_state='green', is_archived=True)
    db.add(company); db.flush()
    for axis in db.query(Axis).all():
        question = Question(axis_id=axis.id, question_text=f'Question {axis.name}', max_score=5)
        db.add(question); db.flush()
        db.add(Answer(company_id=company.id, question_id=question.id, score_code='4', score_value=4))
        db.add(Score(company_id=company.id, axis_id=axis.id, score_percentage=80, score_total=4, score_max=5, answered_questions=1, total_questions=1))
        db.add(CompanyAxis(company_id=company.id, axis_id=axis.id, is_selected=True, show_in_portfolio=True))
    category = AxisQuestionCategory(axis_id=old_axis.id, name='Old category')
    db.add(category); db.flush()
    db.add(AxisQuestionCategory(axis_id=old_axis.id, name='Old sub-category', parent_category_id=category.id))
    scale = ScoringScale(axis_id=old_axis.id, name='Old scale', max_score=5, is_active=False)
    db.add(scale); db.flush()
    db.add(ScoringLevel(scoring_scale_id=scale.id, code='0', score_value=0, label='0', order_index=0))
    db.add(SWOT(company_id=company.id, axis_id=old_axis.id))
    for name in ['Finances', 'Informations Générales']:
        section = CompanyProfileSection(name=name, order_index=1)
        db.add(section); db.flush()
        question = CompanyProfileQuestion(section_id=section.id, question_text=f'Profile {name}')
        db.add(question); db.flush()
        db.add(CompanyProfileAnswer(company_id=company.id, question_id=question.id, answer_text='Existing answer'))
    db.commit()
    return company


def test_clean_up_deletes_the_old_axis_and_its_data_and_is_repeatable(configured_db, old_database):
    db = configured_db
    for _ in range(2):
        delete_finance_axis(db); db.commit()

    assert [a.name for a in db.query(Axis).order_by(Axis.order_index)] == SIX_AXES
    assert [a.order_index for a in db.query(Axis).order_by(Axis.order_index)] == [1, 2, 3, 4, 5, 6]
    # Everything linked to the old axis is gone...
    assert db.query(AxisQuestionCategory).count() == 0
    assert db.query(ScoringScale).filter_by(name='Old scale').count() == 0
    assert db.query(SWOT).count() == 0
    assert [s.name for s in db.query(CompanyProfileSection)] == ['Informations Générales']
    # ...and the data of the six axes is kept.
    assert db.query(Question).count() == db.query(Answer).count() == 6
    assert db.query(Score).count() == db.query(CompanyAxis).count() == 6
    assert db.query(CompanyProfileAnswer).count() == 1


def test_swot_context_uses_the_six_axes(configured_db, old_database):
    db = configured_db
    delete_finance_axis(db); db.commit()
    swot = build_swot_context(db, old_database.id)
    assert len(swot['selected_axes']) == len(swot['axis_scores']) == 6
    assert [q['section'] for q in swot['company_profile']] == ['Informations Générales']


def test_company_selection_radar_and_scores_use_the_six_axes(configured_db, old_database):
    from app.routers.company_axes import get_company_axes_selection, get_diagnostic_overview
    from app.routers.scores import get_company_scores, calculate_company_scores, get_archive_average_scores
    from app.routers.company_profile import get_company_profile_questions, admin_get_company_profile_sections, admin_get_company_profile_questions
    db = configured_db; company = old_database
    delete_finance_axis(db); db.commit()
    user = SimpleNamespace(role='admin')
    assert len(get_company_axes_selection(company.id, db, user)) == 6
    assert len(get_diagnostic_overview(company.id, db, user)) == 6
    assert len(get_company_scores(company.id, db, user)) == 6
    assert len(get_archive_average_scores(company.id, db, user)) == 6
    assert len(calculate_company_scores(company.id, db, user)) == 6
    assert len(get_company_profile_questions(db, user)) == 1
    assert len(admin_get_company_profile_sections(db, user)) == 1
    assert len(admin_get_company_profile_questions(db, user)) == 1
