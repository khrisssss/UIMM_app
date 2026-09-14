from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_consultant_or_admin
from app.models.company import Company
from app.models.axis import Axis
from app.models.question import Question
from app.models.answer import Answer
from app.models.company_axis import CompanyAxis
from app.schemas.company_axis import CompanyAxisRead, CompanyAxisUpdate, DiagnosticAxisOverview
from app.schemas.question import QuestionRead
from app.models.axis_question_category import AxisQuestionCategory

router = APIRouter(tags=["Company axes"])


def is_rse_axis(axis: Axis) -> bool:
    return "rse" in axis.name.lower()


def question_matches_company_size(question: Question, company_size: str | None) -> bool:
    if company_size == "<10":
        return question.target_less_than_10

    if company_size == "11-50":
        return question.target_11_to_50

    if company_size == ">50":
        return question.target_more_than_50

    return True


def ensure_company_axes_exist(company: Company, db: Session):
    axes = db.query(Axis).order_by(Axis.order_index).all()

    for axis in axes:
        existing = (
            db.query(CompanyAxis)
            .filter(
                CompanyAxis.company_id == company.id,
                CompanyAxis.axis_id == axis.id,
            )
            .first()
        )

        if not existing:
            selected_by_default = True

            if is_rse_axis(axis) and company.has_rse is False:
                selected_by_default = False

            company_axis = CompanyAxis(
                company_id=company.id,
                axis_id=axis.id,
                is_selected=selected_by_default,
            #    for_mission_complementaire=False,
            )

            db.add(company_axis)

    db.commit()


def company_axis_to_read(company_axis: CompanyAxis) -> CompanyAxisRead:
    return CompanyAxisRead(
        id=company_axis.id,
        company_id=company_axis.company_id,
        axis_id=company_axis.axis_id,
        axis_name=company_axis.axis.name,
        axis_description=company_axis.axis.description,
        axis_order_index=company_axis.axis.order_index,
        is_selected=company_axis.is_selected,
      #  for_mission_complementaire=company_axis.for_mission_complementaire,
        created_at=company_axis.created_at,
        updated_at=company_axis.updated_at,
        diagnostic_comment=company_axis.diagnostic_comment
    )


@router.get(
    "/companies/{company_id}/axes-selection",
    response_model=list[CompanyAxisRead],
)
def get_company_axes_selection(
    company_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_consultant_or_admin),
):
    """Read which diagnostic axes are selected for a company."""
    company = db.query(Company).filter(Company.id == company_id).first()

    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    ensure_company_axes_exist(company, db)

    company_axes = (
        db.query(CompanyAxis)
        .join(Axis, CompanyAxis.axis_id == Axis.id)
        .filter(CompanyAxis.company_id == company_id)
        .order_by(Axis.order_index)
        .all()
    )

    return [company_axis_to_read(item) for item in company_axes]


@router.patch(
    "/companies/{company_id}/axes-selection/{axis_id}",
    response_model=CompanyAxisRead,
)
def update_company_axis_selection(
    company_id: int,
    axis_id: int,
    axis_update: CompanyAxisUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_consultant_or_admin),
):
    """Update a company axis selection and the supplied diagnostic information."""
    company = db.query(Company).filter(Company.id == company_id).first()

    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    ensure_company_axes_exist(company, db)

    company_axis = (
        db.query(CompanyAxis)
        .filter(
            CompanyAxis.company_id == company_id,
            CompanyAxis.axis_id == axis_id,
        )
        .first()
    )

    if not company_axis:
        raise HTTPException(status_code=404, detail="Company axis not found")

    update_data = axis_update.model_dump(exclude_unset=True)
    print("COMPANY AXIS UPDATE DATA:", update_data)
    for key, value in update_data.items():
        setattr(company_axis, key, value)

    db.commit()
    db.refresh(company_axis)

    return company_axis_to_read(company_axis)


@router.get(
    "/companies/{company_id}/diagnostic-overview",
    response_model=list[DiagnosticAxisOverview],
)
def get_diagnostic_overview(
    company_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_consultant_or_admin),
):
    """Read the company diagnostic overview, including progress across its axes."""
    company = db.query(Company).filter(Company.id == company_id).first()

    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    ensure_company_axes_exist(company, db)

    company_axes = (
        db.query(CompanyAxis)
        .join(Axis, CompanyAxis.axis_id == Axis.id)
        .filter(
            CompanyAxis.company_id == company_id,
            CompanyAxis.is_selected == True,
        )
        .order_by(Axis.order_index)
        .all()
    )

    overview = []

    for company_axis in company_axes:
        questions = (
            db.query(Question)
            .filter(
                Question.axis_id == company_axis.axis_id,
                Question.is_active == True,
            )
            .order_by(Question.order_index)
            .all()
        )

        visible_questions = [
            question
            for question in questions
            if question_matches_company_size(question, company.company_size)
        ]

        question_ids = [question.id for question in visible_questions]

        answered_questions = 0

        if question_ids:
            answered_questions = (
                db.query(Answer)
                .filter(
                    Answer.company_id == company_id,
                    Answer.question_id.in_(question_ids),
                    Answer.score_code.isnot(None),
                )
                .count()
            )

        total_questions = len(visible_questions)

        progress_percentage = (
            0
            if total_questions == 0
            else round((answered_questions / total_questions) * 100)
        )

        overview.append(
            DiagnosticAxisOverview(
                axis_id=company_axis.axis_id,
                axis_name=company_axis.axis.name,
                axis_order_index=company_axis.axis.order_index,
                is_selected=company_axis.is_selected,
              # for_mission_complementaire=company_axis.for_mission_complementaire,
                answered_questions=answered_questions,
                total_questions=total_questions,
                progress_percentage=progress_percentage,
            )
        )

    return overview


@router.get(
    "/companies/{company_id}/diagnostic/axes/{axis_id}/questions",
    response_model=list[QuestionRead],
)
def get_company_axis_questions(
    company_id: int,
    axis_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_consultant_or_admin),
):
    """List the diagnostic questions for this company and axis, applying company-specific question selection."""
    company = db.query(Company).filter(Company.id == company_id).first()

    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    company_axis = (
        db.query(CompanyAxis)
        .filter(
            CompanyAxis.company_id == company_id,
            CompanyAxis.axis_id == axis_id,
            CompanyAxis.is_selected == True,
        )
        .first()
    )

    if not company_axis:
        raise HTTPException(
            status_code=400,
            detail="This axis is not selected for this company",
        )

    questions = (
        db.query(Question)
        .outerjoin(
            AxisQuestionCategory,
            Question.category_id == AxisQuestionCategory.id,
        )
        .filter(
            Question.axis_id == axis_id,
            Question.is_active == True,
        )
        .order_by(
            AxisQuestionCategory.order_index.asc().nullslast(),
            Question.category_id.asc().nullslast(),
            Question.order_index.asc(),
        )
        .all()
    )

    filtered_questions = [
        question
        for question in questions
        if question_matches_company_size(question, company.company_size)
    ]

    result = []

    for question in filtered_questions:
        result.append(
            {
                "id": question.id,
                "axis_id": question.axis_id,
                "category_id": question.category_id,
                "category_name": question.category.name if question.category else None,
                "category_order_index": question.category.order_index if question.category else None,
                "question_text": question.question_text,
                "theme": question.theme,
                "order_index": question.order_index,
                "max_score": question.max_score,
                "is_active": question.is_active,
                "target_less_than_10": question.target_less_than_10,
                "target_11_to_50": question.target_11_to_50,
                "target_more_than_50": question.target_more_than_50,
                "created_at": question.created_at,
                "updated_at": question.updated_at,
            }
        )

    return result