"""Chart of Accounts API Routes"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List
from app.core.database import get_db_session
from app.modules.general_ledger.services.coa_service import CoAService
from app.modules.general_ledger.schemas.coa_schemas import (
    GLAccountCreate,
    GLAccountUpdate,
    GLAccountResponse,
    GLAccountMappingCreate,
    GLAccountMappingResponse
)
from app.core.exceptions import NotFoundError, ValidationError

router = APIRouter(prefix="/books/{book_id}/accounts", tags=["Chart of Accounts"])


@router.post("", response_model=GLAccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    book_id: UUID,
    account: GLAccountCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new GL account"""
    service = CoAService(db)
    try:
        created = await service.create_account(
            book_id=book_id,
            account_code=account.account_code,
            account_name=account.account_name,
            account_type=account.account_type,
            parent_account_id=account.parent_account_id,
            description=account.description
        )
        return created
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=List[GLAccountResponse])
async def list_accounts(
    book_id: UUID,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db_session)
):
    """List all accounts for a book"""
    service = CoAService(db)
    accounts = await service.list_accounts(book_id, active_only=active_only)
    return accounts


@router.get("/{account_id}", response_model=GLAccountResponse)
async def get_account(
    account_id: UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """Get account by ID"""
    service = CoAService(db)
    account = await service.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.patch("/{account_id}", response_model=GLAccountResponse)
async def update_account(
    account_id: UUID,
    account_update: GLAccountUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    """Update account"""
    service = CoAService(db)
    try:
        updated = await service.update_account(
            account_id,
            account_name=account_update.account_name,
            description=account_update.description,
            is_active=account_update.is_active
        )
        return updated
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/mappings", response_model=GLAccountMappingResponse, status_code=status.HTTP_201_CREATED)
async def create_mapping(
    mapping: GLAccountMappingCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """Create or update account mapping"""
    service = CoAService(db)
    try:
        created = await service.create_mapping(
            legal_entity_id=mapping.legal_entity_id,
            book_id=mapping.book_id,
            map_key=mapping.map_key,
            gl_account_id=mapping.gl_account_id
        )
        return created
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/mappings/{map_key}", response_model=GLAccountMappingResponse)
async def get_mapping(
    book_id: UUID,
    map_key: str,
    legal_entity_id: UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """Get account mapping"""
    service = CoAService(db)
    mapping = await service.get_mapping(legal_entity_id, book_id, map_key)
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")
    return mapping
