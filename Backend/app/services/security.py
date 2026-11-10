from datetime import datetime, timedelta, timezone  # tools to work with dates, durations and time zones
from typing import Optional  # "Optional" means a value can also be None (empty)

import os  # gives access to the settings in the environment
from jose import jwt, JWTError  # jwt makes and opens tokens; JWTError = "this token is bad"
from pwdlib import PasswordHash  # the tool that turns a password into a hash
from dotenv import load_dotenv  # reads the .env file



load_dotenv()  # read the .env file so the settings below exist

password_hash = PasswordHash.recommended()  # use the recommended hashing method (Argon2)

SECRET_KEY = os.getenv("SECRET_KEY")  # the secret used to sign tokens; whoever knows it could make fake tokens
ALGORITHM = os.getenv("ALGORITHM", "HS256")  # how tokens are signed; HS256 if nothing is set
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))  # how long a login lasts; 60 minutes by default


def hash_password(password: str) -> str:  # turns "mypassword" into an unreadable hash
    return password_hash.hash(password)  # the hash is stored in the database, never the real password


def verify_password(plain_password: str, hashed_password: str) -> bool:  # checks a typed password against the stored hash
    return password_hash.verify(plain_password, hashed_password)  # True if they match, False if not


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:  # makes the token given at login
    to_encode = data.copy()  # copy the information to put in the token (so we do not change the original)

    if expires_delta is None:  # no special duration was asked
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)  # expires in the usual time
    else:  # a duration was given
        expire = datetime.now(timezone.utc) + expires_delta  # expires after that duration

    to_encode.update({"exp": expire})  # write the expiry date inside the token

    encoded_jwt = jwt.encode(  # build and sign the token
        to_encode,  # what goes inside
        SECRET_KEY,  # signed with our secret, so nobody can change it
        algorithm=ALGORITHM  # with this signing method
    )

    return encoded_jwt  # the token: a long text sent to the frontend

def decode_access_token(token: str) -> dict:  # opens a token and checks it is real and not expired
    try:  # try to open it
        payload = jwt.decode(  # check the signature and the expiry date
            token,  # the token sent by the frontend
            SECRET_KEY,  # the same secret used to sign it
            algorithms=[ALGORITHM]  # only accept our signing method
        )
        return payload  # it is valid: give back what is inside
    except JWTError:  # fake, changed or expired token
        return None  # say "no" by giving back nothing
