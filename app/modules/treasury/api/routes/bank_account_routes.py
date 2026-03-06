"""Bank Account API Routes"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List
from app.core.database import get_db_session
from app.modules.treasury.services.bank_account_service import BankAccountService
from app.modules.treasury.schemas.bank_account_schemas import (
    BankAccountCreate,
    BankAccountUpdate,
    BankAccountResponse
)
from app.core.exceptions import NotFoundError, ValidationError
from app.auth.authorization import get_user_context

router = APIRouter(prefix="/bank-accounts", tags=["Bank Accounts"], dependencies=[Depends(get_user_context)])


@router.post("", response_model=BankAccountResponse, status_code=status.HTTP_201_CREATED)
async def create_bank_account(
    account: BankAccountCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new bank account"""
    service = BankAccountService(db)
    try:
        created = await service.create_account(
            legal_entity_id=account.legal_entity_id,
            account_name=account.account_name,
            bank_name=account.bank_name,
            currency=account.currency,
            account_number=account.account_number,
            bank_code=account.bank_code,
            account_type=account.account_type,
            wps_enabled=account.wps_enabled,
            wps_agent_id=account.wps_agent_id
        )
        return created
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=List[BankAccountResponse])
async def list_bank_accounts(
    entity_id: UUID,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db_session)
):
    """List bank accounts for an entity"""
    service = BankAccountService(db)
    accounts = await service.list_accounts(entity_id, active_only=active_only)
    return accounts


@router.get("/{account_id}", response_model=BankAccountResponse)
async def get_bank_account(
    account_id: UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """Get bank account by ID"""
    service = BankAccountService(db)
    account = await service.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Bank account not found")
    return account


@router.patch("/{account_id}", response_model=BankAccountResponse)
async def update_bank_account(
    account_id: UUID,
    account_update: BankAccountUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    """Update bank account"""
    service = BankAccountService(db)
    try:
        updated = await service.update_account(
            account_id,
            account_name=account_update.account_name,
            is_active=account_update.is_active,
            wps_enabled=account_update.wps_enabled,
            wps_agent_id=account_update.wps_agent_id
        )
        return updated
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
