from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.dependencies.auth import require_admin, require_consultant_or_admin
from app.models.company import Company
from app.models.company_profile_section import CompanyProfileSection
from app.models.company_profile_question import CompanyProfileQuestion
from app.models.company_profile_answer import CompanyProfileAnswer
from app.schemas.company_profile import (
    CompanyProfileSectionCreate,
    CompanyProfileSectionUpdate,
    CompanyProfileSectionRead,
    CompanyProfileQuestionCreate,
    CompanyProfileQuestionUpdate,
    CompanyProfileQuestionRead,
    CompanyProfileAnswerCreate,
    CompanyProfileAnswerRead,
)

router = APIRouter(tags=["Company profile questionnaire"])


def question_to_read(question: CompanyProfileQuestion) -> CompanyProfileQuestionRead:
    return CompanyProfileQuestionRead(
        id=question.id,
        section_id=question.section_id,
        section_name=question.section.name,
        section_order_index=question.section.order_index,
        question_text=question.question_text,
        order_index=question.order_index,
        is_active=question.is_active,
        created_at=question.created_at,
        updated_at=question.updated_at,
    )

def get_next_section_order_index(db: Session) -> int:
    sections = db.query(CompanyProfileSection).all()

    if not sections:
        return 1

    return max(section.order_index for section in sections) + 1


def get_next_question_order_index_for_section(db: Session, section_id: int) -> int:
    questions = (
        db.query(CompanyProfileQuestion)
        .filter(CompanyProfileQuestion.section_id == section_id)
        .all()
    )

    if not questions:
        return 1

    return max(question.order_index for question in questions) + 1

# -----------------------------
# Sections
# -----------------------------

@router.get(
    "/company-profile-sections",
    response_model=list[CompanyProfileSectionRead],
)
def get_active_company_profile_sections(
    db: Session = Depends(get_db),
    current_user=Depends(require_consultant_or_admin),
):
    """List active sections of the company profile questionnaire."""
    return (
        db.query(CompanyProfileSection)
        .filter(CompanyProfileSection.is_active == True)
        .order_by(CompanyProfileSection.order_index)
        .all()
    )


@router.get(
    "/admin/company-profile-sections",
    response_model=list[CompanyProfileSectionRead],
)
def admin_get_company_profile_sections(
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """List company profile sections for administration."""
    return (
        db.query(CompanyProfileSection)
        .filter(~func.lower(func.trim(CompanyProfileSection.name)).in_(['finance', 'finances']))
        .order_by(CompanyProfileSection.order_index)
        .all()
    )


@router.post(
    "/admin/company-profile-sections",
    response_model=CompanyProfileSectionRead,
)
def create_company_profile_section(
    section: CompanyProfileSectionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """Create a section to group company profile questions."""
    new_section = CompanyProfileSection(
        name=section.name,
        order_index=get_next_section_order_index(db),
        is_active=True,
    )

    db.add(new_section)
    db.commit()
    db.refresh(new_section)

    return new_section


@router.patch(
    "/admin/company-profile-sections/{section_id}",
    response_model=CompanyProfileSectionRead,
)
def update_company_profile_section(
    section_id: int,
    section_update: CompanyProfileSectionUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """Edit a company profile section."""
    db_section = (
        db.query(CompanyProfileSection)
        .filter(CompanyProfileSection.id == section_id)
        .first()
    )

    if not db_section:
        raise HTTPException(status_code=404, detail="Section not found")

    update_data = section_update.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        if key in ["order_index", "is_active"]:   #editing a section only edits the name.
            continue

        setattr(db_section, key, value)

    db.commit()
    db.refresh(db_section)

    return db_section


@router.delete("/admin/company-profile-sections/{section_id}")  #delete will do a cascade
def delete_company_profile_section(
    section_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """Delete a company profile section and its associated questions and answers."""
    db_section = (
        db.query(CompanyProfileSection)
        .filter(CompanyProfileSection.id == section_id)
        .first()
    )

    if not db_section:
        raise HTTPException(status_code=404, detail="Section not found")

    questions_in_section = (
        db.query(CompanyProfileQuestion)
        .filter(CompanyProfileQuestion.section_id == section_id)
        .all()
    )

    question_ids = [question.id for question in questions_in_section]

    deleted_answers_count = 0

    if question_ids:
        deleted_answers_count = (
            db.query(CompanyProfileAnswer)
            .filter(CompanyProfileAnswer.question_id.in_(question_ids))
            .delete(synchronize_session=False)
        )

        (
            db.query(CompanyProfileQuestion)
            .filter(CompanyProfileQuestion.id.in_(question_ids))
            .delete(synchronize_session=False)
        )

    db.delete(db_section)
    db.commit()

    return {
        "message": "Section, questions, and profile answers deleted",
        "section_id": section_id,
        "deleted_questions": len(question_ids),
        "deleted_answers": deleted_answers_count,
    }

# -----------------------------
# Profile questions
# -----------------------------

@router.get(
    "/company-profile-questions",
    response_model=list[CompanyProfileQuestionRead],
)
def get_company_profile_questions(
    db: Session = Depends(get_db),
    current_user=Depends(require_consultant_or_admin),
):
    """List company profile questions for completing the company profile."""
    questions = (
        db.query(CompanyProfileQuestion)
        .join(CompanyProfileSection)
        .filter(
            CompanyProfileQuestion.is_active == True,
            CompanyProfileSection.is_active == True,
        )
        .order_by(
            CompanyProfileSection.order_index,
            CompanyProfileQuestion.order_index,
        )
        .all()
    )

    return [question_to_read(question) for question in questions]


@router.get(
    "/admin/company-profile-questions",
    response_model=list[CompanyProfileQuestionRead],
)
def admin_get_company_profile_questions(
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """List company profile questions for administration."""
    questions = (
        db.query(CompanyProfileQuestion)
        .join(CompanyProfileSection)
        .filter(~func.lower(func.trim(CompanyProfileSection.name)).in_(['finance', 'finances']))
        .order_by(
            CompanyProfileSection.order_index,
            CompanyProfileQuestion.order_index,
        )
        .all()
    )

    return [question_to_read(question) for question in questions]


@router.post(
    "/admin/company-profile-questions",
    response_model=CompanyProfileQuestionRead,
)
def create_company_profile_question(
    question: CompanyProfileQuestionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """Create a question in the company profile questionnaire."""
    section = (
        db.query(CompanyProfileSection)
        .filter(CompanyProfileSection.id == question.section_id)
        .first()
    )

    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    new_question = CompanyProfileQuestion(
        section_id=question.section_id,
        question_text=question.question_text,
        order_index=get_next_question_order_index_for_section(db=db, section_id=question.section_id),
        is_active=True,
    )

    db.add(new_question)
    db.commit()
    db.refresh(new_question)

    return question_to_read(new_question)


@router.patch(
    "/admin/company-profile-questions/{question_id}",
    response_model=CompanyProfileQuestionRead,
)
def update_company_profile_question(
    question_id: int,
    question_update: CompanyProfileQuestionUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """Edit a company profile question."""
    db_question = (
        db.query(CompanyProfileQuestion)
        .filter(CompanyProfileQuestion.id == question_id)
        .first()
    )

    if not db_question:
        raise HTTPException(status_code=404, detail="Profile question not found")

    update_data = question_update.model_dump(exclude_unset=True)

    if "section_id" in update_data:
        section = (
            db.query(CompanyProfileSection)
            .filter(CompanyProfileSection.id == update_data["section_id"])
            .first()
        )

        if not section:
            raise HTTPException(status_code=404, detail="Section not found")

    for key, value in update_data.items():
            if key in ["order_index", "is_active"]:   #editing a question only edits the text and section. //section_id and question_text
                continue
        
            setattr(db_question, key, value)

    db.commit()
    db.refresh(db_question)

    return question_to_read(db_question)


@router.delete("/admin/company-profile-questions/{question_id}")
def delete_company_profile_question(
    question_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """Delete a company profile question and its associated answers."""
    db_question = (
        db.query(CompanyProfileQuestion)
        .filter(CompanyProfileQuestion.id == question_id)
        .first()
    )

    if not db_question:
        raise HTTPException(status_code=404, detail="Profile question not found")

    deleted_answers_count = (
        db.query(CompanyProfileAnswer)
        .filter(CompanyProfileAnswer.question_id == question_id)
        .delete(synchronize_session=False)
    )

    db.delete(db_question)
    db.commit()

    return {
        "message": "Profile question and answers deleted",
        "question_id": question_id,
        "deleted_answers": deleted_answers_count,
    }


# -----------------------------
# Company profile answers
# -----------------------------

@router.get(
    "/companies/{company_id}/profile-answers",
    response_model=list[CompanyProfileAnswerRead],
)
def get_company_profile_answers(
    company_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_consultant_or_admin),
):
    """List the company profile answers saved for this company."""
    company = db.query(Company).filter(Company.id == company_id).first()

    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    return (
        db.query(CompanyProfileAnswer)
        .filter(CompanyProfileAnswer.company_id == company_id)
        .all()
    )


@router.post(
    "/companies/{company_id}/profile-answers",
    response_model=CompanyProfileAnswerRead,
)
def create_or_update_company_profile_answer(
    company_id: int,
    answer: CompanyProfileAnswerCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_consultant_or_admin),
):
    """Save a profile answer. Updates the existing answer for this company and question, or creates it if missing."""
    company = db.query(Company).filter(Company.id == company_id).first()

    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    question = (
        db.query(CompanyProfileQuestion)
        .filter(CompanyProfileQuestion.id == answer.question_id)
        .first()
    )

    if not question:
        raise HTTPException(status_code=404, detail="Profile question not found")

    existing_answer = (
        db.query(CompanyProfileAnswer)
        .filter(
            CompanyProfileAnswer.company_id == company_id,
            CompanyProfileAnswer.question_id == answer.question_id,
        )
        .first()
    )

    if existing_answer:
        existing_answer.answer_text = answer.answer_text
        existing_answer.comment = answer.comment

        db.commit()
        db.refresh(existing_answer)

        return existing_answer

    new_answer = CompanyProfileAnswer(
        company_id=company_id,
        question_id=answer.question_id,
        answer_text=answer.answer_text,
        comment=answer.comment,
    )

    db.add(new_answer)
    db.commit()
    db.refresh(new_answer)

    return new_answer
