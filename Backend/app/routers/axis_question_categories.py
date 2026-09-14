from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_admin
from app.models.axis import Axis
from app.models.axis_question_category import AxisQuestionCategory
from app.schemas.axis_question_category import (
    AxisQuestionCategoryCreate,
    AxisQuestionCategoryUpdate,
    AxisQuestionCategoryRead,
)
from app.models.question import Question
from app.models.answer import Answer


router = APIRouter(tags=["Axis question categories"])


def category_to_read(category: AxisQuestionCategory) -> AxisQuestionCategoryRead:
    return AxisQuestionCategoryRead(
        id=category.id,
        axis_id=category.axis_id,
        axis_name=category.axis.name,
        parent_category_id=category.parent_category_id,
        parent_category_name=category.parent_category.name
        if category.parent_category
        else None,
        name=category.name,
        order_index=category.order_index,
        is_active=category.is_active,
        created_at=category.created_at,
        updated_at=category.updated_at,
    )


def get_next_category_order_index(  #Main categories have their own order.Child categories inside one parent have their own order.
    db: Session,
    axis_id: int,
    parent_category_id: int | None = None,
) -> int:
    query = db.query(AxisQuestionCategory).filter(
        AxisQuestionCategory.axis_id == axis_id
    )

    if parent_category_id is None:   
        query = query.filter(AxisQuestionCategory.parent_category_id == None)
    else:
        query = query.filter(
            AxisQuestionCategory.parent_category_id == parent_category_id
        )

    categories = query.all()

    if not categories:
        return 1

    return max(category.order_index for category in categories) + 1

@router.get(
    "/axis-question-categories",
    response_model=list[AxisQuestionCategoryRead],
)
def get_active_axis_question_categories(
    axis_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """List active categories used to organize diagnostic questions."""
    query = (
        db.query(AxisQuestionCategory)
        .join(Axis, AxisQuestionCategory.axis_id == Axis.id)
        .filter(AxisQuestionCategory.is_active == True)
    )

    if axis_id is not None:
        query = query.filter(AxisQuestionCategory.axis_id == axis_id)

    categories = (
        query.order_by(Axis.order_index, AxisQuestionCategory.order_index)
        .all()
    )

    return [category_to_read(category) for category in categories]


@router.get(
    "/admin/axis-question-categories",
    response_model=list[AxisQuestionCategoryRead],
)
def admin_get_axis_question_categories(
    axis_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """List diagnostic question categories for administration, using the supplied filters."""
    query = db.query(AxisQuestionCategory).join(
        Axis,
        AxisQuestionCategory.axis_id == Axis.id,
    )

    if axis_id is not None:
        query = query.filter(AxisQuestionCategory.axis_id == axis_id)

    categories = (
        query.order_by(Axis.order_index, AxisQuestionCategory.order_index)
        .all()
    )

    return [category_to_read(category) for category in categories]


@router.post(
    "/admin/axis-question-categories",
    response_model=AxisQuestionCategoryRead,
)

def create_axis_question_category(
    category: AxisQuestionCategoryCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """Create a category for diagnostic questions under an axis.

    {
      "axis_id": 7,
      "parent_category_id": null, # add null when theres no parent category and its like the title 
      "name": "Gouvernance et Stratégie",
      "order_index": 1,
      "is_active": true
    }"""
    axis = db.query(Axis).filter(Axis.id == category.axis_id).first()

    if not axis:
        raise HTTPException(status_code=404, detail="Axis not found")

    if category.parent_category_id is not None:
        parent_category = (
            db.query(AxisQuestionCategory)
            .filter(AxisQuestionCategory.id == category.parent_category_id)
            .first()
        )

        if not parent_category:
            raise HTTPException(status_code=404, detail="Parent category not found")

        if parent_category.axis_id != category.axis_id:
            raise HTTPException(
                status_code=400,
                detail="Parent category must belong to the same axis",
            )

    order_index = get_next_category_order_index(
        db=db,
        axis_id=category.axis_id,
        parent_category_id=category.parent_category_id,
        ) #So the backend will ignore manual order when creating a category.

    new_category = AxisQuestionCategory(
        axis_id=category.axis_id,
        parent_category_id=category.parent_category_id,
        name=category.name,
        order_index=order_index,
        is_active=category.is_active,
    )

    db.add(new_category)
    db.commit()
    db.refresh(new_category)

    return category_to_read(new_category)


@router.patch(
    "/admin/axis-question-categories/{category_id}",
    response_model=AxisQuestionCategoryRead,
)
def update_axis_question_category(
    category_id: int,
    category_update: AxisQuestionCategoryUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """Edit a diagnostic question category using the supplied fields.

    To to edit a category's name"""
    """{
        "name": "Gouvernance et stratégie RSE",
        "order_index": 1,
        "is_active": true
        }"""
    """ To move a category under s parent category"""
    """{
        "parent_category_id": 5
        }"""
    """To make a main category"""
    """{
       "parent_category_id": null
       }"""
    db_category = (
        db.query(AxisQuestionCategory)
        .filter(AxisQuestionCategory.id == category_id)
        .first()
    )

    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")

    update_data = category_update.model_dump(exclude_unset=True)

    new_axis_id = update_data.get("axis_id", db_category.axis_id)
    new_parent_category_id = update_data.get(
        "parent_category_id",
        db_category.parent_category_id,
    )

    axis = db.query(Axis).filter(Axis.id == new_axis_id).first()

    if not axis:
        raise HTTPException(status_code=404, detail="Axis not found")

    if new_parent_category_id is not None:
        parent_category = (
            db.query(AxisQuestionCategory)
            .filter(AxisQuestionCategory.id == new_parent_category_id)
            .first()
        )

        if not parent_category:
            raise HTTPException(status_code=404, detail="Parent category not found")

        if parent_category.axis_id != new_axis_id:
            raise HTTPException(
                status_code=400,
                detail="Parent category must belong to the same axis",
            )

        if parent_category.id == category_id:
            raise HTTPException(
                status_code=400,
                detail="A category cannot be its own parent",
            )


    parent_changed = (
        new_axis_id != db_category.axis_id
        or new_parent_category_id != db_category.parent_category_id
    )

    if "axis_id" in update_data:
        db_category.axis_id = update_data["axis_id"]

    if "parent_category_id" in update_data:
        db_category.parent_category_id = update_data["parent_category_id"]

    if "name" in update_data:
        db_category.name = update_data["name"]

    if "is_active" in update_data:
        db_category.is_active = update_data["is_active"]

    # Do not allow manual order_index editing.
    # If category is moved to another axis or parent, place it at the end.
    if parent_changed:
        db_category.order_index = get_next_category_order_index(
            db=db,
            axis_id=new_axis_id,
            parent_category_id=new_parent_category_id,
        )
    db.commit()
    db.refresh(db_category)

    return category_to_read(db_category)


@router.delete("/admin/axis-question-categories/{category_id}")
def deactivate_axis_question_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """Deactivate a question category instead of permanently deleting it.

    just todeactivate the category and its questions, not to delete them permanently"""
    category = (
        db.query(AxisQuestionCategory)
        .filter(AxisQuestionCategory.id == category_id)
        .first()
    )

    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    category.is_active = False

    questions_in_category = (
        db.query(Question)
        .filter(Question.category_id == category_id)
        .all()
    )

    for question in questions_in_category:
        question.is_active = False

    db.commit()

    return {
        "message": "Category and questions deactivated",
        "category_id": category_id,
        "deactivated_questions": len(questions_in_category),
    }

@router.delete("/admin/axis-question-categories/{category_id}/hard-delete")
def hard_delete_axis_question_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """Permanently delete a question category and the associated records handled by this endpoint.

    to delete permamently the category and its questions and answers"""
    """ find the questions inside the category, delete answers for thise questions, delete questions, delete category"""
    category = (
        db.query(AxisQuestionCategory)
        .filter(AxisQuestionCategory.id == category_id)
        .first()
    )

    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    questions_in_category = (
        db.query(Question)
        .filter(Question.category_id == category_id)
        .all()
    )

    question_ids = [question.id for question in questions_in_category]

    deleted_answers_count = 0

    if question_ids:
        deleted_answers_count = (
            db.query(Answer)
            .filter(Answer.question_id.in_(question_ids))
            .delete(synchronize_session=False)
        )

        (
            db.query(Question)
            .filter(Question.id.in_(question_ids))
            .delete(synchronize_session=False)
        )

    db.delete(category)
    db.commit()

    return {
        "message": "Category, questions, and answers permanently deleted",
        "category_id": category_id,
        "deleted_questions": len(question_ids),
        "deleted_answers": deleted_answers_count,
    }

@router.patch("/admin/axis-question-categories/{axis_id}/reorder")
def reorder_axis_question_categories(
    axis_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """Save the display order of question categories within an axis."""
    parent_category_id = payload.get("parent_category_id")
    ordered_category_ids = payload.get("ordered_category_ids", [])

    axis = db.query(Axis).filter(Axis.id == axis_id).first()

    if not axis:
        raise HTTPException(status_code=404, detail="Axis not found")

    query = db.query(AxisQuestionCategory).filter(
        AxisQuestionCategory.axis_id == axis_id
    )

    if parent_category_id is None:
        query = query.filter(AxisQuestionCategory.parent_category_id == None)
    else:
        parent_category = (
            db.query(AxisQuestionCategory)
            .filter(AxisQuestionCategory.id == parent_category_id)
            .first()
        )

        if not parent_category:
            raise HTTPException(status_code=404, detail="Parent category not found")

        if parent_category.axis_id != axis_id:
            raise HTTPException(
                status_code=400,
                detail="Parent category must belong to the selected axis",
            )

        query = query.filter(
            AxisQuestionCategory.parent_category_id == parent_category_id
        )

    categories = query.all()

    category_ids_for_group = {category.id for category in categories}

    if set(ordered_category_ids) != category_ids_for_group:
        raise HTTPException(
            status_code=400,
            detail="The reorder list must contain all categories for this group.",
        )

    category_by_id = {category.id: category for category in categories}

    for index, category_id in enumerate(ordered_category_ids, start=1):
        category_by_id[category_id].order_index = index

    db.commit()

    return {"message": "Categories reordered"} 