from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserRead
from app.services.security import hash_password
from app.dependencies.auth import require_admin


router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


@router.post("/", response_model=UserRead)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Create a user account with a password, role, and active status."""
    existing_user = (
        db.query(User)
        .filter(User.username == user_data.username)
        .first()
    )

    if existing_user is not None:
        raise HTTPException(
            status_code=400,
            detail="Username already exists"
        )

    if user_data.role not in ["admin", "consultant"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid role"
        )

    new_user = User(
        full_name=user_data.full_name,
        username=user_data.username,
        hashed_password=hash_password(user_data.password),
        role=user_data.role,
        is_active=user_data.is_active
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.get("/", response_model=list[UserRead])
def get_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """List user accounts for administration."""
    users = (
        db.query(User)
        .order_by(User.id)
        .all()
    )

    return users


@router.patch("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Edit the supplied account fields for an existing user."""
    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if user_data.username is not None:
        existing_user = (
            db.query(User)
            .filter(
                User.username == user_data.username,
                User.id != user_id
            )
            .first()
        )

        if existing_user is not None:
            raise HTTPException(
                status_code=400,
                detail="Username already exists"
            )

        user.username = user_data.username

    if user_data.full_name is not None:
        user.full_name = user_data.full_name

    if user_data.password is not None:
        user.hashed_password = hash_password(user_data.password)

    if user_data.role is not None:
        if user_data.role not in ["admin", "consultant"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid role"
            )

        user.role = user_data.role

    if user_data.is_active is not None:
        user.is_active = user_data.is_active

    db.commit()
    db.refresh(user)

    return user


@router.patch("/{user_id}/deactivate", response_model=UserRead)
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Deactivate a user account to prevent login."""
    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    user.is_active = False

    db.commit()
    db.refresh(user)

    return user


@router.patch("/{user_id}/activate", response_model=UserRead)
def activate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Reactivate an existing user account."""
    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    user.is_active = True

    db.commit()
    db.refresh(user)

    return user

@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Permanently delete a user account. The currently logged-in user cannot delete their own account."""
    if current_user.id == user_id:
        raise HTTPException(
            status_code=400,
            detail="You cannot delete your own account while logged in.",
        )

    db_user = db.query(User).filter(User.id == user_id).first()

    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(db_user)
    db.commit()

    return {"message": "User deleted successfully"}