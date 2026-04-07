from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from scout.api.deps import get_current_user, get_db
from scout.api.schemas.user import UserCreate, UserCreateResponse, UserResponse
from scout.core.auth import generate_api_key, hash_api_key
from scout.db.models.user import User

router = APIRouter()


@router.post("", response_model=UserCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_user(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    # Check if email already exists
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    api_key = generate_api_key()
    user = User(
        email=payload.email,
        name=payload.name,
        api_key_hash=hash_api_key(api_key),
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    return UserCreateResponse(
        user=UserResponse.model_validate(user),
        api_key=api_key,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(user: User = Depends(get_current_user)):
    return UserResponse.model_validate(user)
