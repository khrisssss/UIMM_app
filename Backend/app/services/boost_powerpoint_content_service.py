import ast
import json
from sqlalchemy import func

from app.models.answer import Answer
from app.models.question import Question
from app.models.axis import Axis
from app.models.company import Company
from app.models.company_axis import CompanyAxis
from app.models.company_profile_answer import CompanyProfileAnswer
from app.models.company_profile_question import CompanyProfileQuestion
from app.models.reports import Report
from app.models.score import Score
from app.models.swot import SWOT


def clean_text(value):
    if value is None:
        return ""

    return str(value).strip()


def parse_swot_value(value):
    if isinstance(value, str):
        text = value.strip()
        if text.startswith(("{", "[")):
            for loader in (json.loads, ast.literal_eval):
                try:
                    return loader(text)
                except (ValueError, SyntaxError, TypeError):
                    pass
    return value


def split_lines(value):
    value = parse_swot_value(value)
    if isinstance(value, dict):
        return [
            axis + " : " + item
            for axis, values in value.items()
            for item in split_lines(values)
        ]
    if isinstance(value, (list, tuple)):
        return [item for value_item in value for item in split_lines(value_item)]
    text = clean_text(value)
    if not text:
        return []
    return [
        line.strip().lstrip("-•").strip()
        for line in text.replace("•", "\n").splitlines()
        if line.strip().lstrip("-•").strip()
    ]


def axis_swot_items(value, axis_name):
    parsed = parse_swot_value(value)
    if isinstance(parsed, dict):
        return split_lines(next(
            (items for name, items in parsed.items() if name.casefold() == axis_name.casefold()),
            [],
        ))
    return [
        item for item in split_lines(parsed)
        if item.casefold().startswith(axis_name.casefold() + " :")
    ]


def limit_items(items, maximum=6):
    clean_items = []

    for item in items:
        cleaned_item = clean_text(item)

        if cleaned_item:
            clean_items.append(cleaned_item)

    return clean_items[:maximum]


def get_axis_scores(db, company_id):
    rows = (
        db.query(Score, Axis)
        .join(Axis, Score.axis_id == Axis.id)
        .join(CompanyAxis, CompanyAxis.axis_id == Axis.id)
        .filter(Score.company_id == company_id, CompanyAxis.company_id == company_id, CompanyAxis.is_selected == True)
        .order_by(Axis.order_index)
        .all()
    )

    scores = []

    for score, axis in rows:
        scores.append(
            {
                "axis_id": axis.id,
                "axis_name": axis.name,
                "score_percentage": round(float(score.score_percentage or 0), 1),
                "score_obtained": float(score.score_total or 0),
                "score_maximum": float(score.score_max or 0),
            }
        )

    return scores


def get_selected_report_axes(db, company_id, scores):
    """SWOT coverage follows selected axes, independently of score availability."""
    rows = (
        db.query(Axis)
        .join(CompanyAxis, CompanyAxis.axis_id == Axis.id)
        .filter(CompanyAxis.company_id == company_id, CompanyAxis.is_selected == True)
        .order_by(Axis.order_index)
        .all()
    )
    scores_by_id = {item["axis_id"]: item for item in scores}
    return [
        {
            "axis_id": axis.id,
            "axis_name": axis.name,
            "score_percentage": scores_by_id.get(axis.id, {}).get("score_percentage"),
        }
        for axis in rows
    ]


def regroup_axis_swot(swot_by_axis):
    """The letter pages are another view of the same axis findings."""
    grouped = {key: [] for key in ("strengths", "weaknesses", "opportunities", "threats")}
    for axis in swot_by_axis:
        name = axis["axis_name"]
        for category in grouped:
            for item in axis.get(category, []):
                text = clean_text(item)
                if text:
                    # Older saved findings may already carry their axis prefix.
                    if text.casefold().startswith(name.casefold() + " :"):
                        text = text.split(":", 1)[1].strip()
                    grouped[category].append(name + " : " + text)
    return grouped


def get_archive_averages(db, scores):
    axis_ids = [item["axis_id"] for item in scores]
    if not axis_ids:
        return {}
    rows = (
        db.query(Score.axis_id, func.avg(Score.score_percentage))
        .join(Company, Score.company_id == Company.id)
        .filter(Company.is_archived == True, Score.axis_id.in_(axis_ids))
        .group_by(Score.axis_id)
        .all()
    )
    return {axis_id: round(float(average), 1) for axis_id, average in rows if average is not None}


def get_axis_comments(db, company_id):
    rows = (
        db.query(CompanyAxis, Axis)
        .join(Axis, CompanyAxis.axis_id == Axis.id)
        .filter(CompanyAxis.company_id == company_id)
        .order_by(Axis.order_index)
        .all()
    )

    comments = {}

    for company_axis, axis in rows:
        comments[axis.name] = clean_text(company_axis.diagnostic_comment)

    return comments


def get_profile_answers(db, company_id):
    rows = (
        db.query(CompanyProfileAnswer, CompanyProfileQuestion)
        .join(
            CompanyProfileQuestion,
            CompanyProfileAnswer.question_id == CompanyProfileQuestion.id,
        )
        .filter(CompanyProfileAnswer.company_id == company_id)
        .order_by(CompanyProfileQuestion.order_index)
        .all()
    )

    profile_answers = []

    for answer, question in rows:
        profile_answers.append(
            {
                "question": clean_text(question.question_text),
                "answer": clean_text(answer.answer_text),
                "comment": clean_text(answer.comment),
            }
        )

    return profile_answers


def find_profile_answer(profile_answers, keywords):
    for profile_answer in profile_answers:
        question = profile_answer["question"].lower()

        for keyword in keywords:
            if keyword.lower() in question:
                return profile_answer["answer"] or profile_answer["comment"]

    return ""


def get_latest_swot(db, company_id):
    return (
        db.query(SWOT)
        .filter(SWOT.company_id == company_id, SWOT.axis_id.is_(None))
        .order_by(SWOT.created_at.desc())
        .first()
    )


def get_axis_answers_summary(db, company_id):
    rows = (
        db.query(Answer, Question, Axis)
        .join(Question, Answer.question_id == Question.id)
        .join(Axis, Question.axis_id == Axis.id)
        .filter(Answer.company_id == company_id)
        .all()
    )

    answers_by_axis = {}

    for answer, question, axis in rows:
        axis_name = axis.name

        if axis_name not in answers_by_axis:
            answers_by_axis[axis_name] = []

        answer_text = clean_text(answer.answer_text)
        comment = clean_text(answer.comment)

        if comment or answer_text:
            answers_by_axis[axis_name].append(question.question_text + ' : ' + (answer_text or comment))

    return answers_by_axis


def build_swot_by_axis_from_global_swot(swot, scores, axis_comments, axis_analysis):
    swot_by_axis = []
    for score in scores:
        axis_name = score["axis_name"]
        findings = next((value for name, value in axis_analysis.items()
                         if name.casefold() == axis_name.casefold()), {})
        if not isinstance(findings, dict):
            findings = {}
        swot_by_axis.append({
            "axis_name": axis_name,
            "score_percentage": score["score_percentage"],
            "comment": axis_comments.get(axis_name, ""),
            **{
                category: limit_items(findings.get(category, []), 5)
                or limit_items(axis_swot_items(getattr(swot, category, None), axis_name), 5)
                for category in ("strengths", "weaknesses", "opportunities", "threats")
            },
        })
    return swot_by_axis


def build_boost_powerpoint_content(db, company: Company, report: Report):
    profile_answers = get_profile_answers(db, company.id)
    scores = get_axis_scores(db, company.id)
    axis_comments = get_axis_comments(db, company.id)
    swot = get_latest_swot(db, company.id)

    company_history = find_profile_answer(
        profile_answers,
        ["historique", "history", "created", "founded", "création"],
    )

    company_activity = find_profile_answer(
        profile_answers,
        ["activité", "activity", "business", "sector", "secteur"],
    )

    company_managers = find_profile_answer(
        profile_answers,
        ["dirigeant", "manager", "management", "leader", "direction"],
    )

    initial_expectation = find_profile_answer(
        profile_answers,
        ["attente", "expectation", "besoin", "need", "objectif"],
    )

    company_situation = find_profile_answer(
        profile_answers,
        ["situation", "contexte", "context"],
    )

    governance = find_profile_answer(
        profile_answers,
        ["gouvernance", "governance", "organisation", "organization"],
    )

    future_outlook = find_profile_answer(
        profile_answers,
        ["avenir", "future", "perspective", "projection"],
    )

    external_interviews = find_profile_answer(
        profile_answers,
        ["interview externe", "external interview", "client", "customer"],
    )

    internal_interviews = find_profile_answer(
        profile_answers,
        ["interview interne", "internal interview", "salarié", "employee"],
    )

    magic_wand = find_profile_answer(
        profile_answers,
        ["baguette magique", "magic wand"],
    )

    captured_signals = find_profile_answer(
        profile_answers,
        ["signaux", "signals", "observations", "captured"],
    )


    try:
        axis_analysis = json.loads(report.axis_analysis or '{}')
    except (ValueError, TypeError):
        axis_analysis = {}
    if not isinstance(axis_analysis, dict):
        axis_analysis = {}

    swot_by_axis = build_swot_by_axis_from_global_swot(
        swot=swot,
        scores=get_selected_report_axes(db, company.id, scores),
        axis_comments=axis_comments,
        axis_analysis=axis_analysis,
    )

    global_swot = regroup_axis_swot(swot_by_axis)

    try:
        presentation = json.loads(report.presentation_content or "{}")
    except (ValueError, TypeError):
        presentation = {}
    if not isinstance(presentation, dict):
        presentation = {}

    content = {
        "company_name": clean_text(company.name),
        "company_size": clean_text(company.company_size),
        "company_status": clean_text(company.status),
        "general_state": clean_text(company.general_state),
        "cover_title": f"Dossier : {clean_text(company.name)}",
        "objectives": [
            "Réaliser un diagnostic 360",
            "Identifier les leviers d’actions prioritaires",
            "Actionner la mission complémentaire si nécessaire",
        ],
        "company_presentation": {
            "history": clean_text(presentation.get("history")) or company_history or "Information à compléter.",
            "activity": clean_text(presentation.get("activity")) or company_activity or "Information à compléter.",
            "managers": clean_text(presentation.get("managers")) or company_managers or "Information à compléter.",
        },
        "company_issues": {
            "initial_expectation": clean_text(presentation.get("initial_expectation")) or initial_expectation or "Information à compléter.",
            "situation": clean_text(presentation.get("situation")) or company_situation or clean_text(report.executive_summary),
            "governance": clean_text(presentation.get("governance")) or governance or "Information à compléter.",
            "future": clean_text(presentation.get("future")) or future_outlook or "Information à compléter.",
        },
        "interviews": {
            "external": split_lines(external_interviews),
            "internal_words": split_lines(internal_interviews),
            "magic_wand": split_lines(magic_wand),
            "captured_signals": split_lines(captured_signals),
        },
        "swot_by_axis": swot_by_axis,
        "global_swot": global_swot,
        "radar_scores": scores,
        "archive_average_scores": get_archive_averages(db, scores),
        "synthesis": {
            "diagnostic_summary": clean_text(report.diagnostic_summary),
            "recommendations_text": clean_text(report.recommendations),
            "recommendations": split_lines(report.recommendations),
            "conclusion": clean_text(report.conclusion),
            "priority_action_levers": limit_items(
                split_lines(report.recommendations),
                6,
            ),
            "complementary_mission": clean_text(report.conclusion)
            or "Proposition de mission complémentaire à compléter.",
        },
        "resource_people": "Personnes ressources à compléter.",
    }

    return content