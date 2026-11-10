from fastapi import APIRouter, HTTPException, Depends  # tools to make routes, send errors, and get dependencies
from fastapi.security import HTTPBearer  # reads the "Bearer <token>" header
from sqlalchemy.orm import Session  # the type of a database session

from app.database import get_db  # gives us a database session
from app.models.user import User  # the users table
from app.schemas.auth import LoginRequest, LoginResponse  # the shape of what we receive and send back
from app.services.security import verify_password, create_access_token  # check passwords and make tokens



router = APIRouter(  # a group of routes
    prefix="/auth",  # every route here starts with /auth
    tags=["Auth"]  # the section name in the /docs page
)

bearer_scheme = HTTPBearer()  # the token reader (kept for the /docs page)

@router.post("/login", response_model=LoginResponse)  # the route POST /auth/login; the answer has the LoginResponse shape
def login(
    login_data: LoginRequest,  # the username and password sent by the login page
    db: Session = Depends(get_db)  # a database session
):
    """Check the username and password and return an access token and user information. Inactive accounts cannot log in."""
    user = db.query(User).filter(User.username == login_data.username).first()  # find the user with this username

    if user is None:  # nobody has this username
        raise HTTPException(  # stop and send an error
            status_code=401,  # not logged in
            detail="Invalid username or password"  # same message as a wrong password, so attackers cannot guess usernames
        )

    if user.is_active is False:  # the account was switched off by an admin
        raise HTTPException(
            status_code=403,  # not allowed
            detail="User account is inactive"
        )

    password_is_valid = verify_password(  # compare the typed password with the stored hash
        login_data.password,  # what the person typed
        user.hashed_password  # the hash saved in the database
    )

    if password_is_valid is False:  # the password is wrong
        raise HTTPException(
            status_code=401,  # not logged in
            detail="Invalid username or password"
        )

    access_token = create_access_token(  # everything is right: make a token for this user
        data={  # what we write inside the token
            "sub": user.username,  # who the user is
            "user_id": user.id,  # their number in the database
            "role": user.role  # admin or consultant
        }
    )

    return {  # the answer sent to the login page
        "access_token": access_token,  # the token the frontend will send with every request
        "token_type": "bearer",  # the kind of token
        "user": user  # the user's information (name, role...) for the interface
    }
