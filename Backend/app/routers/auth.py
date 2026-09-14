from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse
from app.services.security import verify_password, create_access_token
from app.dependencies.auth import get_current_user



router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)

bearer_scheme = HTTPBearer()

@router.post("/login", response_model=LoginResponse)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """Check the username and password and return an access token and user information. Inactive accounts cannot log in."""
    user = db.query(User).filter(User.username == login_data.username).first()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    if user.is_active is False:
        raise HTTPException(
            status_code=403,
            detail="User account is inactive"
        )

    password_is_valid = verify_password(
        login_data.password,
        user.hashed_password
    )

    if password_is_valid is False:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    access_token = create_access_token(
        data={
            "sub": user.username,
            "user_id": user.id,
            "role": user.role
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }
