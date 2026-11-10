"""Read-only company export. Identifying information stays inside the application."""
from datetime import date, datetime
from decimal import Decimal
from collections import defaultdict

from app.models.company import Company
from app.models.company_profile_section import CompanyProfileSection
from app.models.company_profile_question import CompanyProfileQuestion
from app.models.company_profile_answer import CompanyProfileAnswer
from app.models.axis import Axis
from app.models.company_axis import CompanyAxis
from app.models.axis_question_category import AxisQuestionCategory
from app.models.question import Question
from app.models.answer import Answer
from app.models.scoring_scale import ScoringScale
from app.models.scoring_level import ScoringLevel
from app.models.score import Score
from app.models.swot import SWOT
from app.models.reports import Report


def record_details(record):
    """Serialize columns only, avoiding relationship loading and preserving exact amounts."""
    if record is None:
        return None
    result = {}
    for column in record.__table__.columns:
        value = getattr(record, column.key)
        if isinstance(value, (date, datetime)):
            value = value.isoformat()
        elif isinstance(value, Decimal):
            value = str(value)
        result[column.key] = value
    return result


def group_records(records, key):
    grouped = defaultdict(list)
    for record in records:
        grouped[getattr(record, key)].append(record)
    return grouped


def build_company_details(db, company_id):
    company = db.query(Company).filter(Company.id == company_id).first()
    if company is None:
        return None

    # Include inactive and unanswered questions for a complete inventory.
    sections = db.query(CompanyProfileSection).order_by(
        CompanyProfileSection.order_index, CompanyProfileSection.id
    ).all()
    profile_questions = group_records(db.query(CompanyProfileQuestion).order_by(
        CompanyProfileQuestion.order_index, CompanyProfileQuestion.id
    ).all(), "section_id")
    profile_answers = group_records(db.query(CompanyProfileAnswer).filter(
        CompanyProfileAnswer.company_id == company_id
    ).order_by(CompanyProfileAnswer.id).all(), "question_id")
    profile = []
    for section in sections:
        questions = []
        for question in profile_questions[section.id]:
            answers = profile_answers[question.id]
            questions.append({
                "question": record_details(question),
                "answer": record_details(answers[-1]) if answers else None,
                "answers": [record_details(answer) for answer in answers],
            })
        profile.append({"section": record_details(section), "questions": questions})

    axes = db.query(Axis).order_by(Axis.order_index, Axis.id).all()
    selections = group_records(db.query(CompanyAxis).filter(
        CompanyAxis.company_id == company_id
    ).order_by(CompanyAxis.id).all(), "axis_id")
    questions_by_axis = group_records(db.query(Question).order_by(
        Question.order_index, Question.id
    ).all(), "axis_id")
    answers_by_question = group_records(db.query(Answer).filter(
        Answer.company_id == company_id
    ).order_by(Answer.id).all(), "question_id")
    categories = group_records(db.query(AxisQuestionCategory).order_by(
        AxisQuestionCategory.order_index, AxisQuestionCategory.id
    ).all(), "axis_id")
    scales = group_records(db.query(ScoringScale).order_by(ScoringScale.id).all(), "axis_id")
    levels = group_records(db.query(ScoringLevel).order_by(
        ScoringLevel.order_index, ScoringLevel.id
    ).all(), "scoring_scale_id")
    scores = db.query(Score).filter(Score.company_id == company_id).order_by(
        Score.axis_id, Score.id
    ).all()
    scores_by_axis = group_records(scores, "axis_id")

    diagnostic = []
    for axis in axes:
        scale_details = [
            {**record_details(scale), "levels": [record_details(level) for level in levels[scale.id]]}
            for scale in scales[axis.id]
        ]
        questions = []
        for question in questions_by_axis[axis.id]:
            answers = answers_by_question[question.id]
            questions.append({
                "question": record_details(question),
                "answer": record_details(answers[-1]) if answers else None,
                "answers": [record_details(answer) for answer in answers],
            })
        selection = selections[axis.id]
        diagnostic.append({
            "axis": record_details(axis),
            "selection": record_details(selection[-1]) if selection else None,
            "is_selected": bool(selection and selection[-1].is_selected),
            "categories": [record_details(item) for item in categories[axis.id]],
            "scoring_scales": scale_details,
            "questions": questions,
            "scores": [record_details(item) for item in scores_by_axis[axis.id]],
        })

    return {
        "company": record_details(company),
        "profile": profile,
        "axes": diagnostic,
        "scores": [record_details(item) for item in scores],
        "swots": [record_details(item) for item in db.query(SWOT).filter(
            SWOT.company_id == company_id
        ).order_by(SWOT.created_at.desc(), SWOT.id.desc()).all()],
        "reports": [record_details(item) for item in db.query(Report).filter(
            Report.company_id == company_id
        ).order_by(Report.created_at.desc(), Report.id.desc()).all()],
    }
