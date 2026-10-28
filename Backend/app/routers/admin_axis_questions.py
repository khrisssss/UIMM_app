from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_admin
from app.models.axis import Axis
from app.models.answer import Answer
from app.models.axis_question_category import AxisQuestionCategory
from app.models.question import Question
#from app.schemas.question import QuestionCreate, QuestionUpdate, AdminQuestionRead
from app.models.scoring_scale import ScoringScale
from app.schemas.question import (
    QuestionCreate, 
    QuestionUpdate, 
    AdminQuestionRead,
    ReorderAxisQuestionsRequest,
)


router = APIRouter(tags=["Admin axis questions"])


def question_to_admin_read(question: Question) -> AdminQuestionRead:
    return AdminQuestionRead(
        id=question.id,
        axis_id=question.axis_id,
        axis_name=question.axis.name,
        axis_order_index=question.axis.order_index,
        category_id=question.category_id,
        category_name=question.category.name if question.category else None,
        category_order_index=question.category.order_index
        if question.category
        else None,
        question_text=question.question_text,
        theme=None,
        order_index=question.order_index,
        max_score=question.max_score,
        is_active=question.is_active,
        target_less_than_10=question.target_less_than_10,
        target_11_to_50=question.target_11_to_50,
        target_more_than_50=question.target_more_than_50,
        created_at=question.created_at,
        updated_at=question.updated_at,
    )


def get_next_order_index_for_axis_category(
    db: Session,
    axis_id: int,
    category_id: int | None,
) -> int:
    query = db.query(Question).filter(Question.axis_id == axis_id)

    if category_id is None:
        query = query.filter(Question.category_id == None)
    else:
        query = query.filter(Question.category_id == category_id)

    questions = query.all()

    if not questions:
        return 1

    return max(question.order_index for question in questions) + 1


def validate_category_for_axis(
    db: Session,
    axis_id: int,
    category_id: int | None,
):
    if category_id is None:
        return

    category = (
        db.query(AxisQuestionCategory)
        .filter(AxisQuestionCategory.id == category_id)
        .first()
    )

    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    if category.axis_id != axis_id:
        raise HTTPException(
            status_code=400,
            detail="Category must belong to the selected axis",
        )


@router.get("/admin/axis-questions", response_model=list[AdminQuestionRead])
def get_admin_axis_questions(
    axis_id:int | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """Administrateur | List diagnostic questions for administration, using the supplied filters."""
    query = (
        db.query(Question)
        .join(Axis, Question.axis_id == Axis.id)
    )

    if axis_id is not None:
        query = query.filter(Question.axis_id == axis_id)

    questions = (
        query
        .order_by(
            Axis.order_index,
            Question.category_id,
            Question.order_index,
        )
        .all()
    )

    return [question_to_admin_read(question) for question in questions]


@router.post("/admin/axis-questions", response_model=AdminQuestionRead)
def create_axis_question(
    question: QuestionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """Administrateur | Create a diagnostic question with its scoring and company-size settings."""
    axis = db.query(Axis).filter(Axis.id == question.axis_id).first()

    if not axis:
        raise HTTPException(status_code=404, detail="Axis not found")

    validate_category_for_axis(
        db=db,
        axis_id=question.axis_id,
        category_id=question.category_id,
    )

    next_order_index = get_next_order_index_for_axis_category(
        db=db,
        axis_id=question.axis_id,
        category_id=question.category_id,
    )
    automatic_max_score = get_axis_max_score(    # if the admin creates a question under RSE, backend will automatically store max_score=3
    db=db,
    axis_id=question.axis_id,
    fallback_max_score=question.max_score or 5,
    )
    new_question = Question(
        axis_id=question.axis_id,
        category_id=question.category_id,
        question_text=question.question_text,
        theme=None,
        order_index=next_order_index,
        max_score=automatic_max_score,
        is_active=question.is_active,
        target_less_than_10=question.target_less_than_10,
        target_11_to_50=question.target_11_to_50,
        target_more_than_50=question.target_more_than_50,
    )

    db.add(new_question)
    db.commit()
    db.refresh(new_question)

    return question_to_admin_read(new_question)


@router.patch("/admin/axis-questions/{question_id}", response_model=AdminQuestionRead)
def update_axis_question(
    question_id: int,
    question_update: QuestionUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """Administrateur | Edit a diagnostic question using the supplied fields."""
    db_question = db.query(Question).filter(Question.id == question_id).first()

    if not db_question:
        raise HTTPException(status_code=404, detail="Question not found")

    update_data = question_update.model_dump(exclude_unset=True)

    new_axis_id = update_data.get("axis_id", db_question.axis_id)
    new_category_id = update_data.get("category_id", db_question.category_id)

    axis = db.query(Axis).filter(Axis.id == new_axis_id).first()

    if not axis:
        raise HTTPException(status_code=404, detail="Axis not found")

    validate_category_for_axis(
        db=db,
        axis_id=new_axis_id,
        category_id=new_category_id,
    )

    category_changed = (
        new_axis_id != db_question.axis_id
        or new_category_id != db_question.category_id
    )
    axis_changed = new_axis_id != db_question.axis_id

    for key, value in update_data.items():
        if key in ["theme", "order_index", "max_score"]:   # will ignore theme, order_index, and max_score ??????
            continue

        setattr(db_question, key, value)

    db_question.theme = None

    if axis_changed:     #So if a question is moved from Performance to RSE, the backend automatically changes max score from 5 to 3
        db_question.max_score = get_axis_max_score(
            db=db,
            axis_id=new_axis_id,
            fallback_max_score=db_question.max_score or 5,
        )

    if category_changed:
        db_question.order_index = get_next_order_index_for_axis_category(
            db=db,
            axis_id=new_axis_id,
            category_id=new_category_id,
        )

    db.commit()
    db.refresh(db_question)

    return question_to_admin_read(db_question)


@router.delete("/admin/axis-questions/{question_id}")
def deactivate_axis_question(
    question_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """Deactivate a diagnostic question instead of permanently deleting it.

    This is only to deactivate the question and hide it from the users """
    db_question = db.query(Question).filter(Question.id == question_id).first()

    if not db_question:
        raise HTTPException(status_code=404, detail="Question not found")

    db_question.is_active = False
    db.commit()

    return {"message": "Axis question deactivated"}

@router.delete("/admin/axis-questions/{question_id}/hard-delete")
def hard_delete_axis_question(
    question_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """Permanently delete a diagnostic question and its associated answers.

    This is to permanently delete the question and its answers from the database """
    db_question = db.query(Question).filter(Question.id == question_id).first()

    if not db_question:
        raise HTTPException(status_code=404, detail="Question not found")

    deleted_answers_count = (
        db.query(Answer)
        .filter(Answer.question_id == question_id)
        .delete(synchronize_session=False)
    )

    db.delete(db_question)
    db.commit()

    return {
        "message": "Question permanently deleted",
        "question_id": question_id,
        "deleted_answers": deleted_answers_count,
    }

@router.patch("/admin/axis-questions/{axis_id}/reorder")
def reorder_axis_questions(
    axis_id: int,
    payload: ReorderAxisQuestionsRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """Save the display order of diagnostic questions within an axis.

    To change question order  """
    """ {
        "category_id": 12,
        "ordered_question_ids": [31, 29, 30]
        }"""
    """ that means 
    Question 31 → order 1
    Question 29 → order 2
    Question 30 → order 3"""
    """This only reorders questions inside the same category."""
    category_id = payload.category_id
    ordered_question_ids = payload.ordered_question_ids

    if not ordered_question_ids:
        raise HTTPException(
            status_code=400,
            detail="ordered_question_ids cannot be empty.",
        )

    axis = db.query(Axis).filter(Axis.id == axis_id).first()

    if not axis:
        raise HTTPException(status_code=404, detail="Axis not found")

    query = db.query(Question).filter(Question.axis_id == axis_id)

    if category_id is None:
        query = query.filter(Question.category_id == None)
    else:
        validate_category_for_axis(
            db=db,
            axis_id=axis_id,
            category_id=category_id,
        )
        query = query.filter(Question.category_id == category_id)

    all_questions_in_group = query.order_by(Question.order_index).all()

    question_by_id = {
        question.id: question for question in all_questions_in_group
    }

    invalid_question_ids = [
        question_id
        for question_id in ordered_question_ids
        if question_id not in question_by_id
    ]

    if invalid_question_ids:
        raise HTTPException(
            status_code=400,
            detail=f"These questions do not belong to this axis/category: {invalid_question_ids}",
        )

    final_ordered_ids = []

    for question_id in ordered_question_ids:
        if question_id not in final_ordered_ids:
            final_ordered_ids.append(question_id)

    for question in all_questions_in_group:
        if question.id not in final_ordered_ids:
            final_ordered_ids.append(question.id)

    for index, question_id in enumerate(final_ordered_ids, start=1):
        question_by_id[question_id].order_index = index

    db.commit()

    return {
        "message": "Questions reordered",
        "category_id": category_id,
        "ordered_question_ids": final_ordered_ids,
    }

def get_axis_max_score(db: Session, axis_id: int, fallback_max_score: int = 5) -> int:
    scoring_scale = (
        db.query(ScoringScale)
        .filter(
            ScoringScale.axis_id == axis_id,
            ScoringScale.is_active == True,
        )
        .first()
    )

    if scoring_scale is None:
        return fallback_max_score

    return scoring_scale.max_score