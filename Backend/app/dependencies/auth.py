from fastapi import HTTPException, Depends  # HTTPException = send an error back; Depends = "run this first"
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials  # reads the "Authorization: Bearer <token>" header
from sqlalchemy.orm import Session  # the type of a database session

from app.database import get_db  # gives us a database session
from app.models.user import User  # the users table
from app.services.security import decode_access_token  # opens a token and checks it is real


bearer_scheme = HTTPBearer()  # the rule: every protected request must send a token


def get_current_user(  # finds WHO is making the request, from their token
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),  # FastAPI takes the token from the request header
    db: Session = Depends(get_db)  # FastAPI gives us a database session
):
    token = credentials.credentials  # the token itself (a long text)

    payload = decode_access_token(token)  # open the token; None if it is fake or expired

    if payload is None:  # the token could not be opened
        raise HTTPException(  # stop here and answer with an error
            status_code=401,  # 401 = "you are not logged in"
            detail="Invalid or expired token"  # the message the frontend receives
        )

    username = payload.get("sub")  # "sub" (subject) is the username written inside the token at login

    if username is None:  # the token has no username inside
        raise HTTPException(
            status_code=401,  # not logged in
            detail="Invalid token payload"
        )

    user = db.query(User).filter(User.username == username).first()  # look for this user in the users table

    if user is None:  # the user was deleted after the token was made
        raise HTTPException(
            status_code=401,  # not logged in
            detail="User not found"
        )

    if user.is_active is False:  # an admin switched this account off
        raise HTTPException(
            status_code=403,  # 403 = "we know you, but you are not allowed"
            detail="User account is inactive"
        )

    return user  # everything is fine: give the user to the route


def require_admin(  # only lets admins through
    current_user: User = Depends(get_current_user)  # first find who is asking (function above)
):
    if current_user.role != "admin":  # the user is not an admin
        raise HTTPException(
            status_code=403,  # not allowed
            detail="Admin access required"
        )

    return current_user  # it is an admin: let them in


def require_consultant_or_admin(  # lets consultants and admins through
    current_user: User = Depends(get_current_user)  # first find who is asking
):
    if current_user.role not in ["consultant", "admin"]:  # the role is neither of the two
        raise HTTPException(
            status_code=403,  # not allowed
            detail="Consultant or admin access required"
        )

    return current_user  # the role is right: let them in
