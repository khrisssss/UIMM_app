import ast
import json

from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.company_axis import CompanyAxis
from app.models.axis import Axis
from app.models.question import Question
from app.models.answer import Answer
from app.models.score import Score
from app.models.swot import SWOT
from app.models.company_profile_section import CompanyProfileSection
from app.models.company_profile_question import CompanyProfileQuestion
from app.models.company_profile_answer import CompanyProfileAnswer


def normalize_list_value(value):
    if value is None:
        return []
    if isinstance(value, str) and value.strip().startswith(("{", "[")):
        for loader in (json.loads, ast.literal_eval):
            try:
                value = loader(value)
                break
            except (ValueError, SyntaxError, TypeError):
                pass
    if isinstance(value, dict):
        return [
            str(axis) + " : " + str(item)
            for axis, entries in value.items()
            for item in (entries if isinstance(entries, list) else [entries])
            if str(item).strip()
        ]
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return [str(value)] if str(value).strip() else []


def build_report_context(company_id: int, db: Session) -> dict | None:
    company = db.query(Company).filter(Company.id == company_id).first()

    if company is None:
        return None

    selected_axes_rows = (
        db.query(CompanyAxis, Axis)
        .join(Axis, CompanyAxis.axis_id == Axis.id)
        .filter(
            CompanyAxis.company_id == company_id,
            CompanyAxis.is_selected == True,
        )
        .order_by(Axis.order_index)
        .all()
    )

    scores_rows = (
        db.query(Score, Axis)
        .join(Axis, Score.axis_id == Axis.id)
        .join(CompanyAxis, CompanyAxis.axis_id == Axis.id)
        .filter(Score.company_id == company_id, CompanyAxis.company_id == company_id, CompanyAxis.is_selected == True)
        .order_by(Axis.order_index)
        .all()
    )

    profile_answer_rows = (
        db.query(
            CompanyProfileAnswer,
            CompanyProfileQuestion,
            CompanyProfileSection,
        )
        .join(
            CompanyProfileQuestion,
            CompanyProfileAnswer.question_id == CompanyProfileQuestion.id,
        )
        .join(
            CompanyProfileSection,
            CompanyProfileQuestion.section_id == CompanyProfileSection.id,
        )
        .filter(CompanyProfileAnswer.company_id == company_id)
        .order_by(
            CompanyProfileSection.order_index,
            CompanyProfileQuestion.order_index,
        )
        .all()
    )

    diagnostic_answer_rows = (
        db.query(Answer, Question, Axis)
        .join(Question, Answer.question_id == Question.id)
        .join(Axis, Question.axis_id == Axis.id)
        .filter(Answer.company_id == company_id)
        .order_by(
            Axis.order_index,
            Question.category_id,
            Question.order_index,
        )
        .all()
    )

    latest_swot = (
        db.query(SWOT)
        .filter(SWOT.company_id == company_id, SWOT.axis_id.is_(None))
        .order_by(SWOT.created_at.desc())
        .first()
    )

    selected_axes = []
    for company_axis, axis in selected_axes_rows:
        selected_axes.append(
            {
                "axis_id": axis.id,
                "axis_name": axis.name,
                "diagnostic_comment": company_axis.diagnostic_comment,
            }
        )

    scores = []
    for score, axis in scores_rows:
        scores.append(
            {
                "axis_id": axis.id,
                "axis_name": axis.name,
                "score_total": score.score_total,
                "score_max": score.score_max,
                "score_percentage": score.score_percentage,
                "answered_questions": score.answered_questions,
                "total_questions": score.total_questions,
            }
        )

    company_profile = []
    for answer, question, section in profile_answer_rows:
        company_profile.append(
            {
                "section": section.name,
                "question": question.question_text,
                "answer": answer.answer_text,
                "comment": answer.comment,
            }
        )

    diagnostic_answers = []
    for answer, question, axis in diagnostic_answer_rows:
        diagnostic_answers.append(
            {
                "axis": axis.name,
                "question": question.question_text,
                "score_code": answer.score_code,
                "score_value": answer.score_value,
                "comment": answer.comment,
                "answer_text": answer.answer_text,
            }
        )

    swot = None

    if latest_swot:
        swot = {
            "strengths": normalize_list_value(latest_swot.strengths),
            "weaknesses": normalize_list_value(latest_swot.weaknesses),
            "opportunities": normalize_list_value(latest_swot.opportunities),
            "threats": normalize_list_value(latest_swot.threats),
            "status": latest_swot.status,
            "generation_source": latest_swot.generation_source,
        }

    return {
        "company": {
            "id": company.id,
            "name": company.name,
            "contact_name": company.contact_name,
            "contact_email": company.contact_email,
            "contact_phone": company.contact_phone,
            "address": company.address,
            "company_size": company.company_size,
            "status": company.status,
            "prediag_origin": company.prediag_origin,
            "prediag_origin_other": company.prediag_origin_other,
            "has_rse": company.has_rse,
            "specific_regulatory_constraints": company.specific_regulatory_constraints,
            "general_comment": company.general_comment,
            "diagnostic_referent": company.diagnostic_referent,
            "diagnostic_launch_date": str(company.diagnostic_launch_date)
            if company.diagnostic_launch_date
            else None,
            "diagnostic_restitution_date": str(company.diagnostic_restitution_date)
            if company.diagnostic_restitution_date
            else None,
        },
        "selected_axes": selected_axes,
        "scores": scores,
        "company_profile": company_profile,
        "diagnostic_answers": diagnostic_answers,
        "swot": swot,
    }