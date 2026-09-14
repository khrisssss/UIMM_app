from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str

class UserLoginRead(BaseModel):
    id: int
    full_name: str
    username: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True

class LoginResponse(BaseModel):
#    id: int
#    full_name: str
#    username: str
#    role: str
#    is_active: bool

#    class Config:
#        from_attributes = True

    access_token: str
    token_type: str = "bearer"
    user: UserLoginRead