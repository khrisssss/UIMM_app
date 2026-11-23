"""Delete the old Finance axis and everything linked to it.

UIMM Boost has six diagnostic axes. Databases created before this change may still contain a
seventh axis, Finance, with its questions, answers, scores, SWOTs and a Finance profile section.
This one-time clean-up deletes them for good. It runs at every start and does nothing once they
are gone (idempotent). The caller owns the transaction.
"""
from sqlalchemy import delete, func, select, update

from app.models.answer import Answer
from app.models.axis import Axis
from app.models.axis_question_category import AxisQuestionCategory
from app.models.company_axis import CompanyAxis
from app.models.company_profile_answer import CompanyProfileAnswer
from app.models.company_profile_question import CompanyProfileQuestion
from app.models.company_profile_section import CompanyProfileSection
from app.models.question import Question
from app.models.score import Score
from app.models.scoring_level import ScoringLevel
from app.models.scoring_scale import ScoringScale
from app.models.swot import SWOT

OLD_NAMES = ["finance", "finances"]


def delete_finance_axis(db):
    finance_axes = select(Axis.id).where(func.lower(func.trim(Axis.name)).in_(OLD_NAMES)).scalar_subquery()
    finance_questions = select(Question.id).where(Question.axis_id.in_(finance_axes)).scalar_subquery()
    finance_scales = select(ScoringScale.id).where(ScoringScale.axis_id.in_(finance_axes)).scalar_subquery()
    finance_sections = (
        select(CompanyProfileSection.id)
        .where(func.lower(func.trim(CompanyProfileSection.name)).in_(OLD_NAMES))
        .scalar_subquery()
    )
    finance_profile_questions = (
        select(CompanyProfileQuestion.id)
        .where(CompanyProfileQuestion.section_id.in_(finance_sections))
        .scalar_subquery()
    )

    # Children first, so that no row points to a deleted row.
    db.execute(delete(Answer).where(Answer.question_id.in_(finance_questions)))
    db.execute(delete(Question).where(Question.axis_id.in_(finance_axes)))
    db.execute(update(AxisQuestionCategory).where(AxisQuestionCategory.axis_id.in_(finance_axes)).values(parent_category_id=None))
    db.execute(delete(AxisQuestionCategory).where(AxisQuestionCategory.axis_id.in_(finance_axes)))
    db.execute(delete(ScoringLevel).where(ScoringLevel.scoring_scale_id.in_(finance_scales)))
    db.execute(delete(ScoringScale).where(ScoringScale.axis_id.in_(finance_axes)))
    db.execute(delete(CompanyAxis).where(CompanyAxis.axis_id.in_(finance_axes)))
    db.execute(delete(Score).where(Score.axis_id.in_(finance_axes)))
    db.execute(delete(SWOT).where(SWOT.axis_id.in_(finance_axes)))
    db.execute(delete(Axis).where(func.lower(func.trim(Axis.name)).in_(OLD_NAMES)))

    db.execute(delete(CompanyProfileAnswer).where(CompanyProfileAnswer.question_id.in_(finance_profile_questions)))
    db.execute(delete(CompanyProfileQuestion).where(CompanyProfileQuestion.section_id.in_(finance_sections)))
    db.execute(delete(CompanyProfileSection).where(func.lower(func.trim(CompanyProfileSection.name)).in_(OLD_NAMES)))

    # Keep the six axes in order 1 to 6.
    for name, order in [("Digitalisation", 5), ("RSE", 6)]:
        db.execute(update(Axis).where(Axis.name == name).values(order_index=order))
