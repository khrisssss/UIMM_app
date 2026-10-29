from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_consultant_or_admin

from sqlalchemy import func

from app.models.company import Company
from app.models.axis import Axis
from app.models.question import Question
from app.models.answer import Answer
from app.models.score import Score
from app.models.company_axis import CompanyAxis

from app.schemas.score import ScoreRead


router = APIRouter(tags=["Scores"])


def question_matches_company_size(question: Question, company_size: str | None) -> bool:
    if company_size == "<10":
        return question.target_less_than_10

    if company_size == "11-50":
        return question.target_11_to_50

    if company_size == ">50":
        return question.target_more_than_50

    return True


@router.get("/companies/{company_id}/scores", response_model=list[ScoreRead])
def get_company_scores(
    company_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_consultant_or_admin),
):
    """Read the saved diagnostic scores for a company."""
    company = db.query(Company).filter(Company.id == company_id).first()

    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    return (
        db.query(Score)
        .join(Axis, Score.axis_id == Axis.id)
        .filter(Score.company_id == company_id, Axis.is_active.is_(True))
        .order_by(Score.axis_id)
        .all()
    )


@router.post(
    "/companies/{company_id}/calculate-scores",
    response_model=list[ScoreRead],
)
def calculate_company_scores(
    company_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_consultant_or_admin),
):
    """Recalculate and save diagnostic axis scores from the company answers."""
    company = db.query(Company).filter(Company.id == company_id).first()

    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Remove old scores first, so the radar only reflects the current selected axes.
    active_axis_ids = db.query(Axis.id).filter(Axis.is_active.is_(True))
    db.query(Score).filter(Score.company_id == company_id, Score.axis_id.in_(active_axis_ids)).delete(synchronize_session=False)
    db.commit()

    selected_company_axes = (
        db.query(CompanyAxis)
        .join(Axis, CompanyAxis.axis_id == Axis.id)
        .filter(
            CompanyAxis.company_id == company_id,
            CompanyAxis.is_selected == True,
            Axis.is_active.is_(True),
        )
        .order_by(Axis.order_index)
        .all()
    )

    calculated_scores = []

    for company_axis in selected_company_axes:
        axis_id = company_axis.axis_id

        all_questions = (
            db.query(Question)
            .filter(
                Question.axis_id == axis_id,
                Question.is_active == True,
            )
            .order_by(Question.order_index)
            .all()
        )

        visible_questions = [
            question
            for question in all_questions
            if question_matches_company_size(question, company.company_size)
        ]

        total_questions = len(visible_questions)

        if total_questions == 0:
            continue

        question_ids = [question.id for question in visible_questions]

        answers = (
            db.query(Answer)
            .filter(
                Answer.company_id == company_id,
                Answer.question_id.in_(question_ids),
            )
            .all()
        )

        answered_questions = len(
            [
                answer
                for answer in answers
                if answer.score_code is not None and answer.score_code != ""
            ]
        )

        score_total = 0

        for answer in answers:
            if answer.score_value is not None:
                score_total += answer.score_value

        score_max = 0

        for question in visible_questions:
            if question.max_score is not None:
                score_max += question.max_score

        score_percentage = (
            0
            if score_max == 0
            else round((score_total / score_max) * 100)
        )

        new_score = Score(
            company_id=company_id,
            axis_id=axis_id,
            score_total=score_total,
            score_max=score_max,
            score_percentage=score_percentage,
            answered_questions=answered_questions,
            total_questions=total_questions,
        )

        db.add(new_score)
        calculated_scores.append(new_score)

    db.commit()

    for score in calculated_scores:
        db.refresh(score)

    return calculated_scores


#add archive average scores endpoint
# For the current company, look at its axes, then calculate the average score for those same axesfrom archived companies only.
@router.get("/companies/{company_id}/scores/archive-average")
def get_archive_average_scores(
    company_id: int,
    db: Session = Depends(get_db),
    current_user= Depends(require_consultant_or_admin),
):
    """Calculate average axis percentages from archived companies for comparison with this company."""
    company = db.query(Company).filter(Company.id == company_id).first()

    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")

    current_scores = (
        db.query(Score)
        .join(Axis, Score.axis_id == Axis.id)
        .filter(Score.company_id == company_id, Axis.is_active.is_(True))
        .all()
    )

    current_axis_ids = [score.axis_id for score in current_scores]

    if not current_axis_ids:
        return []

    archive_average_rows = (
        db.query(
            Score.axis_id,
            Axis.name.label("axis_name"),
            func.avg(Score.score_percentage).label("archive_average_percentage"),
            func.count(Score.id).label("archived_score_count"),
        )
        .join(Company, Score.company_id == Company.id)
        .join(Axis, Score.axis_id == Axis.id)
        .filter(
            Company.is_archived == True,
            Axis.is_active.is_(True),
            Score.axis_id.in_(current_axis_ids),
            Score.score_percentage.isnot(None),
        )
        .group_by(Score.axis_id, Axis.name, Axis.order_index)
        .order_by(Axis.order_index)
        .all()
    )

    return [
        {
            "axis_id": row.axis_id,
            "axis_name": row.axis_name,
            "archive_average_percentage": round(float(row.archive_average_percentage), 1)
            if row.archive_average_percentage is not None
            else 0,
            "archived_score_count": row.archived_score_count,
        }
        for row in archive_average_rows
    ]