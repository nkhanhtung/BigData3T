from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from databases.postsql.database import get_db
from schemas.admin import AdminLogin
from cores.security import create_access_token, verify_password
from fastapi.security import OAuth2PasswordRequestForm
from models.admin import Admin
from cores.redis_client import r
from cores.config import settings
from cores.security import oauth2_scheme


router = APIRouter()

ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

@router.post("/login", response_model= AdminLogin)
def login_admin(form_data:OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(Admin.email == form_data.username).first()
    
    if not admin:
        raise HTTPException(status_code=400, detail="Admin not found")
    
    if form_data.password != admin.password_hash:
        raise HTTPException(status_code=400, detail="Incorrect password")
    
    access_token = create_access_token(data={"sub": admin.admin_email})

    old_token = r.get(f"Admin:{admin.admin_email}:token")
    if old_token:
        r.delete(old_token)
    
    r.set(f"admin:{admin.admin_email}:token", access_token,ex=ACCESS_TOKEN_EXPIRE_MINUTES)
    return AdminLogin(
        admin_name=admin.admin_name,
        admin_email=admin.admin_email,
        access_token=access_token,
        token_type="bearer"
    )


@router.post("/logout")
def logout_admin(token: str = Depends(oauth2_scheme)):
    try:
        payload = decode_access_token(token)
        admin_email = payload.get("sub")
        if not admin_email:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        r.delete(token)
        r.delete(f"user:{admin_email}:token")

        return {"message" : "Logout successfully"}
    
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

