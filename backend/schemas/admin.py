from pydantic import BaseModel, EmailStr

class AdminLogin(BaseModel):
    admin_name: str
    admin_email: EmailStr
    current_token: str
    token_type: str

