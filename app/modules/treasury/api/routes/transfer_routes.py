"""Transfer API Routes"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import date
from typing import List, Optional
from app.core.database import get_db_session
from app.modules.treasury.services.transfer_service import TransferService
from app.modules.treasury.schemas.transfer_schemas import (
    TransferCreate,
    TransferResponse
)
from app.modules.treasury.models.transfer_model import TransferType
from app.core.exceptions import NotFoundError, ValidationError, DuplicateEntryError

router = APIRouter(prefix="/transfers", tags=["Transfers"])


@router.post("", response_model=TransferResponse, status_code=status.HTTP_201_CREATED)
async def create_transfer(
    transfer: TransferCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """Create a transfer"""
    service = TransferService(db)
    try:
        created = await service.create_transfer(
            legal_entity_id=transfer.legal_entity_id,
            transfer_date=transfer.transfer_date,
            transfer_type=transfer.transfer_type,
            from_bank_account_id=transfer.from_bank_account_id,
            amount=transfer.amount,
            currency=transfer.currency,
            to_bank_account_id=transfer.to_bank_account_id,
            to_entity_id=transfer.to_entity_id,
            description=transfer.description,
            reference_number=transfer.reference_number,
            external_id=transfer.external_id
        )
        return created
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DuplicateEntryError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("", response_model=List[TransferResponse])
async def list_transfers(
    entity_id: UUID,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    transfer_type: Optional[TransferType] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db_session)
):
    """List transfers for an entity"""
    service = TransferService(db)
    transfers = await service.list_transfers(
        entity_id=entity_id,
        start_date=start_date,
        end_date=end_date,
        transfer_type=transfer_type,
        limit=limit,
        offset=offset
    )
    return transfers


@router.get("/{transfer_id}", response_model=TransferResponse)
async def get_transfer(
    transfer_id: UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """Get transfer by ID"""
    service = TransferService(db)
    transfer = await service.get_transfer(transfer_id)
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer not found")
    return transfer
