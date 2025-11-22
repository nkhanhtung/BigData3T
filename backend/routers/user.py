
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession 
from fastapi.security import OAuth2PasswordRequestForm
from cores.security import create_access_token, verify_password, hash_password, oauth2_scheme, decode_access_token 
from fastapi import Body
from schemas.user import UserCreate, UserLogin
from databases.postsql.database import get_async_session 
from databases.mongodb.database import get_login_user_logs_collection, get_logout_user_logs_collection
from cores.config import settings, settings_redis
from cores.redis_client import get_redis_client 
from models.user import User
from jose import JWTError 
import aioredis
from sqlalchemy.future import select
from datetime import datetime


router = APIRouter()

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
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_async_session),
    redis_client: aioredis.Redis = Depends(get_redis_client),
    mongo_collection = Depends(get_login_user_logs_collection)
):
    result = await db.execute(
        select(User).where(User.user_email == form_data.username)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not found")
    
    block_key = f"user:{user.user_email}:blocked"
    if await redis_client.exists(block_key):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is temporarily blocked. Try later.")

    if not verify_password(form_data.password, user.password_hash):
        fail_key = f"user:{user.user_email}:failed"
        failed_count = await redis_client.incr(fail_key)
        if failed_count == 1:
            await redis_client.expire(fail_key, settings_redis.FAILED_ATTEMPT_TTL_SECONDS)
        
        if failed_count >= settings_redis.MAX_FAILED_ATTEMPTS:
            await redis_client.set(block_key, "1", ex=settings_redis.BLOCK_TIME_SECONDS)
            await redis_client.delete(fail_key)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Too many failed login attempts. User is blocked for {settings_redis.BLOCK_TIME_MINUTES} minutes."
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect password")

    await redis_client.delete(f"user:{user.user_email}:failed")

    access_token = create_access_token(data={"sub": user.user_email})
    old_token = await redis_client.get(f"user:{user.user_email}:token")
    if old_token:
        await redis_client.delete(old_token)
    await redis_client.set(f"user:{user.user_email}:token", access_token, ex=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)

    await mongo_collection.insert_one({
        "user_email": user.user_email,
        "user_name": user.user_name,
        "login_time": datetime.utcnow(),
        "success": True
    })

    return UserLogin(
        user_name=user.user_name,
        user_email=user.user_email,
        current_token=access_token,
        token_type="bearer"
    )


@router.post("/logout")
async def logout_user(token: str = Depends(oauth2_scheme),
                      redis_client: aioredis.Redis = Depends(get_redis_client),
                      mongo_collection = Depends(get_logout_user_logs_collection)):
    logger.info(f"Received token: {token}")     
    try:
        payload = decode_access_token(token)
        user_email = payload.get("sub")
        if not user_email:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        
        await mongo_collection.insert_one({
        "user_email": user_email,
        "logout_time": datetime.utcnow(),
        "success": True
    }) 
        await redis_client.delete(token)
        await redis_client.delete(f"user:{user_email}:token")

        return {"message" : "Logout successfully"}
    
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")