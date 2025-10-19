
from fastapi import APIRouter, Depends, HTTPException, status 
from sqlalchemy.ext.asyncio import AsyncSession 
from sqlalchemy import select 
from schemas.admin import AdminLogin 
from cores.security import create_access_token, verify_password, decode_access_token 
from fastapi.security import OAuth2PasswordRequestForm
from models.admin import Admin
from cores.redis_client import get_redis_client 
from cores.config import settings
from cores.security import oauth2_scheme
from jose import JWTError
import aioredis

router = APIRouter()

ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

from databases.postsql.database import get_async_session 

@router.post("/login", response_model=AdminLogin)
async def login_admin(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_async_session),
    redis_client: aioredis.Redis = Depends(get_redis_client) 
):
    result = await db.execute(
        select(Admin).where(Admin.admin_email == form_data.username) 
    )
    admin = result.scalar_one_or_none()
    
    if not admin:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admin not found")
    
    if not verify_password(form_data.password, admin.password_hash): 
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect password")
    
    access_token = create_access_token(data={"sub": admin.admin_email})

    old_token_key = f"admin:{admin.admin_email}:token"
    old_token = await redis_client.get(old_token_key) 
    if old_token:
        await redis_client.delete(old_token_key) 
    

    await redis_client.set(
        f"admin:{admin.admin_email}:token",
        access_token,
        ex=ACCESS_TOKEN_EXPIRE_MINUTES * 60 
    )
    return AdminLogin(
        admin_name=admin.admin_name,
        admin_email=admin.admin_email,
        current_token=access_token, 
        token_type="bearer"
    )


@router.post("/logout")

async def logout_admin(
    token: str = Depends(oauth2_scheme),
    redis_client: aioredis.Redis = Depends(get_redis_client) 
):
    try:
        payload = decode_access_token(token) 
        admin_email = payload.get("sub")
        if not admin_email:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        
    
        await redis_client.delete(token) 
        await redis_client.delete(f"admin:{admin_email}:token") 

        return {"message" : "Logout successfully"}
    
    except JWTError: 
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

import aioredis 