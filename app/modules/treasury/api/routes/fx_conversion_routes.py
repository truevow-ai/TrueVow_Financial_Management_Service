"""FX Conversion API Routes"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import date
from typing import List, Optional
from app.core.database import get_db_session
from app.modules.treasury.services.fx_conversion_service import FXConversionService
from app.modules.treasury.schemas.fx_conversion_schemas import (
    FXConversionCreate,
    FXConversionResponse
)
from app.core.exceptions import NotFoundError, ValidationError, DuplicateEntryError

router = APIRouter(prefix="/fx/conversions", tags=["FX Conversions"])


@router.post("", response_model=FXConversionResponse, status_code=status.HTTP_201_CREATED)
async def create_fx_conversion(
    conversion: FXConversionCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """Create an FX conversion"""
    service = FXConversionService(db)
    try:
        created = await service.create_conversion(
            legal_entity_id=conversion.legal_entity_id,
            conversion_date=conversion.conversion_date,
            from_currency=conversion.from_currency,
            to_currency=conversion.to_currency,
            from_amount=conversion.from_amount,
            to_amount=conversion.to_amount,
            exchange_rate=conversion.exchange_rate,
            rate_source=conversion.rate_source,
            from_bank_account_id=conversion.from_bank_account_id,
            to_bank_account_id=conversion.to_bank_account_id,
            description=conversion.description,
            external_id=conversion.external_id
        )
        return created
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DuplicateEntryError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("", response_model=List[FXConversionResponse])
async def list_fx_conversions(
    entity_id: UUID,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db_session)
):
    """List FX conversions for an entity"""
    service = FXConversionService(db)
    conversions = await service.list_conversions(
        entity_id=entity_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset
    )
    return conversions


@router.get("/{conversion_id}", response_model=FXConversionResponse)
async def get_fx_conversion(
    conversion_id: UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """Get FX conversion by ID"""
    service = FXConversionService(db)
    conversion = await service.get_conversion(conversion_id)
    if not conversion:
        raise HTTPException(status_code=404, detail="FX conversion not found")
    return conversion
