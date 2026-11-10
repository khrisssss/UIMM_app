"""Retire the Finance diagnostic without deleting saved company information."""
from sqlalchemy import func, select, update
from app.models.axis import Axis
from app.models.question import Question
from app.models.axis_question_category import AxisQuestionCategory
from app.models.company_axis import CompanyAxis
from app.models.company_profile_section import CompanyProfileSection
from app.models.company_profile_question import CompanyProfileQuestion
from app.models.scoring_scale import ScoringScale


def is_finance_name(value):
    return str(value or '').strip().casefold() in {'finance', 'finances'}


def retire_finance(db):
    """Idempotent soft retirement. The caller owns the transaction.

    Primary keys, answers, scores, SWOTs and saved reports remain
    intact. Active screens use the six remaining axes and profile sections.
    """
    finance_axes = select(Axis.id).where(func.lower(func.trim(Axis.name)).in_(['finance', 'finances']))
    finance_sections = select(CompanyProfileSection.id).where(func.lower(func.trim(CompanyProfileSection.name)).in_(['finance', 'finances']))
    updates = [
        (Axis, Axis.id.in_(finance_axes), {'is_active': False}),
        (Question, Question.axis_id.in_(finance_axes), {'is_active': False}),
        (AxisQuestionCategory, AxisQuestionCategory.axis_id.in_(finance_axes), {'is_active': False}),
        (ScoringScale, ScoringScale.axis_id.in_(finance_axes), {'is_active': False}),
        (CompanyAxis, CompanyAxis.axis_id.in_(finance_axes), {'is_selected': False, 'show_in_portfolio': False}),
        (CompanyProfileSection, CompanyProfileSection.id.in_(finance_sections), {'is_active': False}),
        (CompanyProfileQuestion, CompanyProfileQuestion.section_id.in_(finance_sections), {'is_active': False}),
    ]
    for model, condition, values in updates:
        db.execute(update(model).where(condition).values(**values))
    for name, order in [('Digitalisation', 5), ('RSE', 6)]:
        db.execute(update(Axis).where(Axis.name == name).values(order_index=order))
