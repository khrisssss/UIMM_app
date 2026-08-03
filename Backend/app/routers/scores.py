from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.company import Company
from app.models.axis import Axis
from app.models.question import Question
from app.models.answer import Answer
from app.models.score import Score
from app.schemas.score import ScoreRead


router = APIRouter(
    prefix="/companies",
    tags=["Scores"]
)


@router.post("/{company_id}/calculate-scores", response_model=list[ScoreRead])
def calculate_scores(
    company_id: int,
    db: Session = Depends(get_db)
):
    company = db.query(Company).filter(Company.id == company_id).first()

    if company is None:
        raise HTTPException(
            status_code=404,
            detail="Company not found"
        )

    axes = (
        db.query(Axis)
        .filter(Axis.is_active == True)
        .order_by(Axis.order_index)
        .all()
    )

    calculated_scores = []

    for axis in axes:
        questions = (
            db.query(Question)
            .filter(
                Question.axis_id == axis.id,
                Question.is_active == True
            )
            .all()
        )

        total_questions = len(questions)
        score_total = 0
        score_max = 0
        answered_questions = 0

        for question in questions:
            answer = (
                db.query(Answer)
                .filter(
                    Answer.company_id == company_id,
                    Answer.question_id == question.id
                )
                .first()
            )

            if answer is None:
                continue

            if answer.score_code == "SO":
                continue

            if answer.score_value is None:
                continue

            answered_questions += 1
            score_total += answer.score_value

            if question.max_score is not None:
                score_max += question.max_score

        if score_max > 0:
            score_percentage = round((score_total / score_max) * 100, 2)
        else:
            score_percentage = 0

        existing_score = (
            db.query(Score)
            .filter(
                Score.company_id == company_id,
                Score.axis_id == axis.id
            )
            .first()
        )

        if existing_score is None:
            score = Score(
                company_id=company_id,
                axis_id=axis.id,
                score_total=score_total,
                score_max=score_max,
                score_percentage=score_percentage,
                answered_questions=answered_questions,
                total_questions=total_questions
            )
            db.add(score)
            db.commit()
            db.refresh(score)
            calculated_scores.append(score)
        else:
            existing_score.score_total = score_total
            existing_score.score_max = score_max
            existing_score.score_percentage = score_percentage
            existing_score.answered_questions = answered_questions
            existing_score.total_questions = total_questions

            db.commit()
            db.refresh(existing_score)
            calculated_scores.append(existing_score)

    return calculated_scores


@router.get("/{company_id}/scores", response_model=list[ScoreRead])
def get_scores_by_company(
    company_id: int,
    db: Session = Depends(get_db)
):
    company = db.query(Company).filter(Company.id == company_id).first()

    if company is None:
        raise HTTPException(
            status_code=404,
            detail="Company not found"
        )

    scores = (
        db.query(Score)
        .filter(Score.company_id == company_id)
        .order_by(Score.axis_id)
        .all()
    )

    return scores