from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from cores.security import create_access_token, verify_password
from cores.security import hash_password
from fastapi import Body
from schemas.user import UserCreate, UserLogin
from databases.postsql.database import get_db
from cores.config import settings
from cores.redis_client import r
from cores.security import oauth2_scheme
from models.user import User


router = APIRouter()

ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

@router.post("/register", response_model=UserCreate)
def register_user(user: UserCreate,db: Session = Depends(get_db)):
    if db.query(User).filter(User.user_email == user.user_email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = User(
        user_name = user.user_name,
        user_email = user.user_email,
        password_hash = hash_password(user.password_hash)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login", response_model=UserLogin)
def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_email == form_data.username).first()
    if not user :
        raise HTTPException(status_code=400, detail="User not found")
    
    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect password")
    
    access_token = create_access_token(data={"sub": user.user_email})

    old_token = r.get(f"user:{user.user_email}:token")
    if old_token:
        r.delete(old_token)
    
    r.set(f"user:{user.user_email}:token", access_token,ex=ACCESS_TOKEN_EXPIRE_MINUTES)
    return UserLogin(
        user_name=user.user_name,
        user_email=user.user_email,
        current_token=access_token,
        current_token_type="bearer"
    )

@router.post("/logout")
def logout_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = decode_access_token(token)
        user_email = payload.get("sub")
        if not user_email:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        r.delete(token)
        r.delete(f"user:{user_email}:token")

        return {"message" : "Logout successfully"}
    
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

