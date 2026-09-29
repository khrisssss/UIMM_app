from app.models.company import Company
from app.models.company_profile_answer import CompanyProfileAnswer
from app.models.company_profile_question import CompanyProfileQuestion
from app.models.company_profile_section import CompanyProfileSection
from app.models.company_axis import CompanyAxis
from app.models.axis import Axis
from app.models.question import Question
from app.models.answer import Answer
from app.models.score import Score


def get_percentage(value):
    if value is None:
        return 0

    try:
        return round(float(value), 2)
    except (TypeError, ValueError):
        return 0


def classify_answer_for_swot(answer):
    """
    Simple professional rule:
    - score 4 or 5 = strength evidence
    - score 0, 1, 2 = weakness evidence
    - score 3 = opportunity evidence
    - very low score + risk comment = threat evidence
    """

    if answer.score_value is None:
        return "neutral"

    score_value = int(answer.score_value)
    comment = (answer.comment or "").lower()

    risk_words = [
        "no process",
        "pas de processus",
        "not formalized",
        "non formalisé",
        "manual",
        "manuel",
        "excel",
        "depends on one person",
        "dépend d'une personne",
        "urgent",
        "not followed",
        "pas suivi",
        "not measured",
        "pas mesuré",
        "not shared",
        "pas partagé",
        "regulatory constraint",
        "contrainte réglementaire",
        "lack",
        "manque",
        "absence",
        "risk",
        "risque",
    ]

    has_risk_comment = any(word in comment for word in risk_words)

    if score_value >= 4:
        return "strength"

    if score_value <= 2 and has_risk_comment:
        return "threat"

    if score_value <= 2:
        return "weakness"

    if score_value == 3:
        return "opportunity"

    return "neutral"


def build_swot_context(db, company_id: int):
    company = db.query(Company).filter(Company.id == company_id).first()

    if not company:
        return None

    selected_axes = (
        db.query(CompanyAxis, Axis)
        .join(Axis, CompanyAxis.axis_id == Axis.id)
        .filter(
            CompanyAxis.company_id == company_id,
            CompanyAxis.is_selected == True,
        )
        .order_by(Axis.order_index)
        .all()
    )

    scores = (
        db.query(Score, Axis)
        .join(Axis, Score.axis_id == Axis.id)
        .filter(Score.company_id == company_id)
        .order_by(Axis.order_index)
        .all()
    )

    answers = (
        db.query(Answer, Question, Axis)
        .join(Question, Answer.question_id == Question.id)
        .join(Axis, Question.axis_id == Axis.id)
        .filter(Answer.company_id == company_id)
        .order_by(Axis.order_index, Question.order_index)
        .all()
    )

    profile_answers = (
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

    axis_scores = []

    for score, axis in scores:
        percentage = get_percentage(
            getattr(score, "score_percentage", None)
            or getattr(score, "percentage", None)
        )

        axis_scores.append(
            {
                "axis_id": axis.id,
                "axis_name": axis.name,
                "score_total": getattr(score, "score_total", None),
                "score_max": getattr(score, "score_max", None),
                "percentage": percentage,
                "answered_questions": getattr(score, "answered_questions", None),
            }
        )

    diagnostic_answers = []

    swot_evidence = {
        "strengths": [],
        "weaknesses": [],
        "opportunities": [],
        "threats": [],
        "neutral": [],
    }

    for answer, question, axis in answers:
        swot_type = classify_answer_for_swot(answer)

        evidence_item = {
            "axis_name": axis.name,
            "question_text": question.question_text,
            "score_code": answer.score_code,
            "score_value": answer.score_value,
            "max_score": question.max_score,
            "comment": answer.comment,
            "answer_text": answer.answer_text,
            "suggested_swot_type": swot_type,
        }

        diagnostic_answers.append(evidence_item)

        if swot_type == "strength":
            swot_evidence["strengths"].append(evidence_item)
        elif swot_type == "weakness":
            swot_evidence["weaknesses"].append(evidence_item)
        elif swot_type == "opportunity":
            swot_evidence["opportunities"].append(evidence_item)
        elif swot_type == "threat":
            swot_evidence["threats"].append(evidence_item)
        else:
            swot_evidence["neutral"].append(evidence_item)

    company_profile = []

    for profile_answer, profile_question, profile_section in profile_answers:
        company_profile.append(
            {
                "section": profile_section.name,
                "question": profile_question.question_text,
                "answer": profile_answer.answer_text,
            }
        )

    context = {
        "company": {
            "id": company.id,
            "name": company.name,
            "contact_name": company.contact_name,
            "contact_email": company.contact_email,
            "contact_phone": company.contact_phone,
            "address": company.address,
            "company_size": company.company_size,
            "status": company.status,
            "has_rse": company.has_rse,
            "prediag_origin": company.prediag_origin,
            "specific_regulatory_constraints": company.specific_regulatory_constraints,
            "general_comment": company.general_comment,
        },
        "selected_axes": [
            {
                "axis_id": axis.id,
                "axis_name": axis.name,
                "diagnostic_comment": company_axis.diagnostic_comment,
            }
            for company_axis, axis in selected_axes
        ],
        "axis_scores": axis_scores,
        "company_profile": company_profile,
        "diagnostic_answers": diagnostic_answers,
        "swot_evidence": swot_evidence,
    }

    return context