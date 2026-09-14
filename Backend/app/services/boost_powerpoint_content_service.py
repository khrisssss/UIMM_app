from app.models.answer import Answer
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


def split_lines(value):
    text = clean_text(value)

    if not text:
        return []

    lines = []

    for line in text.replace("•", "\n").split("\n"):
        cleaned_line = line.strip(" -•\t")

        if cleaned_line:
            lines.append(cleaned_line)

    return lines


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
        .filter(Score.company_id == company_id)
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
        .filter(SWOT.company_id == company_id)
        .order_by(SWOT.created_at.desc())
        .first()
    )


def get_axis_answers_summary(db, company_id):
    rows = (
        db.query(Answer, Axis)
        .join(Axis, Answer.axis_id == Axis.id)
        .filter(Answer.company_id == company_id)
        .all()
    )

    answers_by_axis = {}

    for answer, axis in rows:
        axis_name = axis.name

        if axis_name not in answers_by_axis:
            answers_by_axis[axis_name] = []

        answer_text = clean_text(answer.answer_text)
        comment = clean_text(answer.comment)

        if comment:
            answers_by_axis[axis_name].append(comment)
        elif answer_text:
            answers_by_axis[axis_name].append(answer_text)

    return answers_by_axis


def build_swot_by_axis_from_global_swot(swot, scores, axis_comments):
    swot_by_axis = []

    global_strengths = split_lines(swot.strengths if swot else "")
    global_weaknesses = split_lines(swot.weaknesses if swot else "")
    global_opportunities = split_lines(swot.opportunities if swot else "")
    global_threats = split_lines(swot.threats if swot else "")

    for score in scores:
        axis_name = score["axis_name"]
        axis_comment = axis_comments.get(axis_name, "")

        swot_by_axis.append(
            {
                "axis_name": axis_name,
                "score_percentage": score["score_percentage"],
                "comment": axis_comment,
                "strengths": limit_items(
                    [
                        item
                        for item in global_strengths
                        if axis_name.lower() in item.lower()
                    ],
                    5,
                )
                or limit_items([axis_comment], 3),
                "weaknesses": limit_items(
                    [
                        item
                        for item in global_weaknesses
                        if axis_name.lower() in item.lower()
                    ],
                    5,
                ),
                "opportunities": limit_items(
                    [
                        item
                        for item in global_opportunities
                        if axis_name.lower() in item.lower()
                    ],
                    5,
                ),
                "threats": limit_items(
                    [
                        item
                        for item in global_threats
                        if axis_name.lower() in item.lower()
                    ],
                    5,
                ),
            }
        )

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

    global_swot = {
        "strengths": limit_items(split_lines(swot.strengths if swot else ""), 12),
        "weaknesses": limit_items(split_lines(swot.weaknesses if swot else ""), 12),
        "opportunities": limit_items(split_lines(swot.opportunities if swot else ""), 12),
        "threats": limit_items(split_lines(swot.threats if swot else ""), 12),
    }

    swot_by_axis = build_swot_by_axis_from_global_swot(
        swot=swot,
        scores=scores,
        axis_comments=axis_comments,
    )

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
            "history": company_history or "Information à compléter.",
            "activity": company_activity or "Information à compléter.",
            "managers": company_managers or "Information à compléter.",
        },
        "company_issues": {
            "initial_expectation": initial_expectation or "Information à compléter.",
            "situation": company_situation or clean_text(report.executive_summary),
            "governance": governance or "Information à compléter.",
            "future": future_outlook or "Information à compléter.",
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
        "synthesis": {
            "diagnostic_summary": clean_text(report.diagnostic_summary),
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