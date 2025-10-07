from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    user_name: str
    user_email: EmailStr
    password_hash: str

    class Config:
        orm_mode = True

class UserLogin(BaseModel):
    user_name: str
    user_email: EmailStr
    current_token: str
    token_type: str

