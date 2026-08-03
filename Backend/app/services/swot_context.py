from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.axis import Axis
from app.models.question import Question
from app.models.answer import Answer
from app.models.score import Score
from app.models.scoring_scale import ScoringScale
from app.models.scoring_level import ScoringLevel


def build_swot_context(company_id: int, db: Session) -> dict:
    company = db.query(Company).filter(Company.id == company_id).first()

    if company is None:
        raise HTTPException(
            status_code=404,
            detail="Company not found"
        )

    scores = (
        db.query(Score, Axis)
        .join(Axis, Score.axis_id == Axis.id)
        .filter(Score.company_id == company_id)
        .order_by(Axis.order_index)
        .all()
    )

    axis_scores = []

    for score, axis in scores:
        axis_scores.append(
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

    answers = (
        db.query(Answer, Question, Axis)
        .join(Question, Answer.question_id == Question.id)
        .join(Axis, Question.axis_id == Axis.id)
        .filter(Answer.company_id == company_id)
        .order_by(Axis.order_index, Question.order_index)
        .all()
    )

    context_questions = []

    for answer, question, axis in answers:
        scoring_scale = (
            db.query(ScoringScale)
            .filter(
                ScoringScale.axis_id == axis.id,
                ScoringScale.is_active == True
            )
            .first()
        )

        scoring_level = None

        if scoring_scale is not None and answer.score_code is not None:
            scoring_level = (
                db.query(ScoringLevel)
                .filter(
                    ScoringLevel.scoring_scale_id == scoring_scale.id,
                    ScoringLevel.code == answer.score_code
                )
                .first()
            )

        context_questions.append(
            {
                "axis_id": axis.id,
                "axis_name": axis.name,
                "question_id": question.id,
                "question_text": question.question_text,

                "score_code": answer.score_code,
                "score_value": answer.score_value,
                "score_label": scoring_level.label if scoring_level else None,
                "score_description": scoring_level.description if scoring_level else None,

                "max_score": question.max_score,
                "answer_text": answer.answer_text,
                "comment": answer.comment,

                "theme": question.theme,
                "low_score_meaning": question.low_score_meaning,
                "high_score_meaning": question.high_score_meaning,
                "opportunity_hint": question.opportunity_hint,
                "threat_hint": question.threat_hint,
            }
        )

    return {
        "company_id": company.id,
        "company_name": company.name,
        "status": company.status,
        "axis_scores": axis_scores,
        "questions": context_questions
    }