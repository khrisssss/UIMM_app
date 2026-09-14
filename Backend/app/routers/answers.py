from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.company import Company
from app.models.question import Question
from app.models.scoring_scale import ScoringScale
from app.models.scoring_level import ScoringLevel
from app.models.answer import Answer
from app.schemas.answer import AnswerCreate, AnswerRead

from app.models.user import User
from app.dependencies.auth import require_consultant_or_admin


router = APIRouter(
    prefix="/companies",
    tags=["Answers"]
)


@router.post("/{company_id}/answers", response_model=AnswerRead)
def create_or_update_answer(
    company_id: int,
    answer_data: AnswerCreate,
    db: Session = Depends(get_db), current_user: User = Depends(require_consultant_or_admin)
):
    """Save a company response to a diagnostic question, creating or updating its answer and scoring information."""
    company = db.query(Company).filter(Company.id == company_id).first()

    if company is None:
        raise HTTPException(
            status_code=404,
            detail="Company not found"
        )

    question = db.query(Question).filter(Question.id == answer_data.question_id).first()

    if question is None:
        raise HTTPException(
            status_code=404,
            detail="Question not found"
        )

    scoring_scale = (
        db.query(ScoringScale)
        .filter(
            ScoringScale.axis_id == question.axis_id,
            ScoringScale.is_active == True
        )
        .first()
    )

    if scoring_scale is None:
        raise HTTPException(
            status_code=404,
            detail="Scoring scale not found for this question"
        )

    scoring_level = (
        db.query(ScoringLevel)
        .filter(
            ScoringLevel.scoring_scale_id == scoring_scale.id,
            ScoringLevel.code == answer_data.score_code
        )
        .first()
    )

    if scoring_level is None:
        raise HTTPException(
            status_code=400,
            detail="Invalid score code for this question"
        )

    existing_answer = (
        db.query(Answer)
        .filter(
            Answer.company_id == company_id,
            Answer.question_id == answer_data.question_id
        )
        .first()
    )

    if existing_answer is None:
        new_answer = Answer(
            company_id=company_id,
            question_id=answer_data.question_id,
            score_code=answer_data.score_code,
            score_value=scoring_level.score_value,
            answer_text=answer_data.answer_text,
            comment=answer_data.comment
        )

        db.add(new_answer)
        db.commit()
        db.refresh(new_answer)

        return new_answer

    existing_answer.score_code = answer_data.score_code
    existing_answer.score_value = scoring_level.score_value
    existing_answer.answer_text = answer_data.answer_text
    existing_answer.comment = answer_data.comment

    db.commit()
    db.refresh(existing_answer)

    return existing_answer

@router.get("/{company_id}/answers", response_model=list[AnswerRead])
def get_answers_by_company(company_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_consultant_or_admin)):
    """List the diagnostic answers saved for a company."""
    company = db.query(Company).filter(Company.id == company_id).first()

    if company is None:
        raise HTTPException(
            status_code=404,
            detail="Company not found"
        )

    answers = (
        db.query(Answer)
        .filter(Answer.company_id == company_id)
        .order_by(Answer.created_at)
        .all()
    )

    return answers