from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from scout.api.deps import get_current_user, get_db
from scout.db.models.social_account import Platform, SocialAccount
from scout.db.models.user import User

router = APIRouter()


class SocialAccountResponse(BaseModel):
    id: str
    platform: str
    platform_username: str
    is_active: bool

    model_config = {"from_attributes": True}


class ConnectAccountRequest(BaseModel):
    platform: Platform
    platform_user_id: str
    platform_username: str
    access_token: str
    refresh_token: str | None = None


@router.get("/accounts", response_model=list[SocialAccountResponse])
async def list_social_accounts(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SocialAccount).where(SocialAccount.user_id == user.id)
    )
    accounts = result.scalars().all()
    return [SocialAccountResponse.model_validate(a) for a in accounts]


@router.post("/accounts", response_model=SocialAccountResponse, status_code=201)
async def connect_social_account(
    payload: ConnectAccountRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Check if account already connected
    existing = await db.execute(
        select(SocialAccount).where(
            SocialAccount.user_id == user.id,
            SocialAccount.platform == payload.platform,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Platform already connected")

    # In production, encrypt tokens before storage
    from scout.services.crypto import encrypt_token

    account = SocialAccount(
        user_id=user.id,
        platform=payload.platform,
        platform_user_id=payload.platform_user_id,
        platform_username=payload.platform_username,
        access_token_encrypted=encrypt_token(payload.access_token),
        refresh_token_encrypted=encrypt_token(payload.refresh_token) if payload.refresh_token else None,
    )
    db.add(account)
    await db.flush()
    await db.refresh(account)
    return SocialAccountResponse.model_validate(account)


@router.delete("/accounts/{account_id}", status_code=204)
async def disconnect_social_account(
    account_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SocialAccount).where(
            SocialAccount.id == account_id,
            SocialAccount.user_id == user.id,
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    await db.delete(account)
