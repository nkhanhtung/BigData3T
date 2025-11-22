from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession 
from fastapi.security import OAuth2PasswordRequestForm
from cores.security import create_access_token, verify_password, hash_password, oauth2_scheme, decode_access_token 
from fastapi import Body
from schemas.user import UserCreate, UserLogin
from databases.postsql.database import get_async_session 
from cores.config import settings
from cores.redis_client import get_redis_client 
from models.user import User
from jose import JWTError 
import aioredis
from sqlalchemy.future import select

router = APIRouter()

ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

@router.post("/register", response_model=UserCreate)
async def register_user(user: UserCreate, db: AsyncSession = Depends(get_async_session)): 
    result = await db.execute(
        User.__table__.select().where(User.user_email == user.user_email)
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    new_user = User(
        user_name = user.user_name,
        user_email = user.user_email,
        password_hash = hash_password(user.password_hash)
    )
    db.add(new_user)
    await db.commit() 
    await db.refresh(new_user) 
    return new_user

@router.post("/login", response_model=UserLogin)
async def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_async_session),redis_client: aioredis.Redis = Depends(get_redis_client)):
    result = await db.execute(
        select(User).where(User.user_email == form_data.username)
    )
    user = result.scalar_one_or_none()

    if not user :
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not found")
    
    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect password")
    
    access_token = create_access_token(data={"sub": user.user_email, "user_id": str(user.user_id)})
    old_token = await redis_client.get(f"user:{user.user_email}:token")
    if old_token:
        await redis_client.delete(old_token)
    await redis_client.set(f"user:{user.user_email}:token", access_token, ex=ACCESS_TOKEN_EXPIRE_MINUTES)


    return UserLogin(
        user_name=user.user_name,
        user_email=user.user_email,
        current_token=access_token,
        token_type="bearer"
    )

@router.post("/logout")
async def logout_user(token: str = Depends(oauth2_scheme),
                      redis_client: aioredis.Redis = Depends(get_redis_client)):
    try:
        payload = decode_access_token(token)
        user_email = payload.get("sub")
        if not user_email:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        
        # await redis_client.delete(token)
        await redis_client.delete(f"user:{user_email}:token")

        return {"message" : "Logout successfully"}
    
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")