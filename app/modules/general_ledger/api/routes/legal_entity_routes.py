"""Legal Entity API Routes"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.core.database import get_db_session as get_db
from app.modules.general_ledger.models.legal_entity_model import LegalEntity
from app.modules.general_ledger.models.book_model import Book
from app.auth.middleware import get_current_user
# Role checking handled via middleware
from app.auth.authorization import get_user_context
from pydantic import BaseModel

router = APIRouter(prefix="/entities", tags=["Legal Entities"], dependencies=[Depends(get_user_context)])

# Pydantic models for request/response
class LegalEntityCreate(BaseModel):
    code: str
    name: str
    country: str
    functional_currency: str
    is_active: bool = True

class LegalEntityUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    country: Optional[str] = None
    functional_currency: Optional[str] = None
    is_active: Optional[bool] = None

class LegalEntityResponse(BaseModel):
    id: str
    code: str
    name: str
    country: str
    functional_currency: str
    is_active: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

class BookResponse(BaseModel):
    id: str
    legal_entity_id: str
    book_type: str
    name: str
    functional_currency: str
    is_active: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

# Helper function to convert model to response
def legal_entity_to_response(entity: LegalEntity) -> LegalEntityResponse:
    return LegalEntityResponse(
        id=str(entity.id),
        code=entity.code,
        name=entity.name,
        country=entity.country,
        functional_currency=entity.functional_currency,
        is_active=entity.is_active,
        created_at=entity.created_at.isoformat() if entity.created_at else None,
        updated_at=entity.updated_at.isoformat() if entity.updated_at else None
    )

def book_to_response(book: Book) -> BookResponse:
    return BookResponse(
        id=str(book.id),
        legal_entity_id=str(book.legal_entity_id),
        book_type=book.book_type.value if hasattr(book.book_type, 'value') else str(book.book_type),
        name=book.name,
        functional_currency=book.functional_currency,
        is_active=book.is_active,
        created_at=book.created_at.isoformat() if book.created_at else None,
        updated_at=book.updated_at.isoformat() if book.updated_at else None
    )

@router.get("", response_model=List[LegalEntityResponse])
async def get_legal_entities(
    is_active: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get all legal entities"""
    try:
        from sqlalchemy import select
        
        query = select(LegalEntity)
        if is_active is not None:
            query = query.where(LegalEntity.is_active == is_active)
        query = query.order_by(LegalEntity.name)
        
        result = await db.execute(query)
        entities = result.scalars().all()
        
        return [legal_entity_to_response(entity) for entity in entities]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch legal entities: {str(e)}")

@router.get("/{entity_id}", response_model=LegalEntityResponse)
async def get_legal_entity(
    entity_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get a specific legal entity"""
    try:
        from sqlalchemy import select
        
        query = select(LegalEntity).where(LegalEntity.id == entity_id)
        result = await db.execute(query)
        entity = result.scalar_one_or_none()
        
        if not entity:
            raise HTTPException(status_code=404, detail="Legal entity not found")
            
        return legal_entity_to_response(entity)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch legal entity: {str(e)}")

@router.get("/{entity_id}/books", response_model=List[BookResponse])
async def get_entity_books(
    entity_id: str,
    is_active: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get all books for a legal entity"""
    try:
        from sqlalchemy import select
        
        # First verify entity exists
        entity_query = select(LegalEntity).where(LegalEntity.id == entity_id)
        entity_result = await db.execute(entity_query)
        entity = entity_result.scalar_one_or_none()
        
        if not entity:
            raise HTTPException(status_code=404, detail="Legal entity not found")
        
        # Get books
        query = select(Book).where(Book.legal_entity_id == entity_id)
        if is_active is not None:
            query = query.where(Book.is_active == is_active)
        query = query.order_by(Book.name)
        
        result = await db.execute(query)
        books = result.scalars().all()
        
        return [book_to_response(book) for book in books]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch entity books: {str(e)}")

@router.post("", response_model=LegalEntityResponse)
async def create_legal_entity(
    entity_data: LegalEntityCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new legal entity"""
    try:
        # Check permissions - only admins can create entities
        if "admin" not in current_user.get("roles", []) and "finance_head" not in current_user.get("roles", []):
            raise HTTPException(status_code=403, detail="Only administrators can create legal entities")
        
        from sqlalchemy import select
        
        # Check if code already exists
        existing_query = select(LegalEntity).where(LegalEntity.code == entity_data.code)
        existing_result = await db.execute(existing_query)
        if existing_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Legal entity code already exists")
        
        # Create new entity
        new_entity = LegalEntity(
            code=entity_data.code,
            name=entity_data.name,
            country=entity_data.country,
            functional_currency=entity_data.functional_currency,
            is_active=entity_data.is_active
        )
        
        db.add(new_entity)
        await db.commit()
        await db.refresh(new_entity)
        
        return legal_entity_to_response(new_entity)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create legal entity: {str(e)}")

@router.put("/{entity_id}", response_model=LegalEntityResponse)
async def update_legal_entity(
    entity_id: str,
    entity_data: LegalEntityUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update a legal entity"""
    try:
        # Check permissions - only admins can update entities
        if "admin" not in current_user.get("roles", []) and "finance_head" not in current_user.get("roles", []):
            raise HTTPException(status_code=403, detail="Only administrators can update legal entities")
        
        from sqlalchemy import select
        
        # Get existing entity
        query = select(LegalEntity).where(LegalEntity.id == entity_id)
        result = await db.execute(query)
        entity = result.scalar_one_or_none()
        
        if not entity:
            raise HTTPException(status_code=404, detail="Legal entity not found")
        
        # Check if new code already exists (if code is being updated)
        if entity_data.code and entity_data.code != entity.code:
            existing_query = select(LegalEntity).where(LegalEntity.code == entity_data.code)
            existing_result = await db.execute(existing_query)
            if existing_result.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="Legal entity code already exists")
        
        # Update fields
        if entity_data.code is not None:
            entity.code = entity_data.code
        if entity_data.name is not None:
            entity.name = entity_data.name
        if entity_data.country is not None:
            entity.country = entity_data.country
        if entity_data.functional_currency is not None:
            entity.functional_currency = entity_data.functional_currency
        if entity_data.is_active is not None:
            entity.is_active = entity_data.is_active
        
        await db.commit()
        await db.refresh(entity)
        
        return legal_entity_to_response(entity)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update legal entity: {str(e)}")

@router.delete("/{entity_id}")
async def delete_legal_entity(
    entity_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete a legal entity"""
    try:
        # Check permissions - only admins can delete entities
        if "admin" not in current_user.get("roles", []) and "finance_head" not in current_user.get("roles", []):
            raise HTTPException(status_code=403, detail="Only administrators can delete legal entities")
        
        from sqlalchemy import select
        
        # Get existing entity
        query = select(LegalEntity).where(LegalEntity.id == entity_id)
        result = await db.execute(query)
        entity = result.scalar_one_or_none()
        
        if not entity:
            raise HTTPException(status_code=404, detail="Legal entity not found")
        
        # Check if entity has books (soft delete only if no books)
        books_query = select(Book).where(Book.legal_entity_id == entity_id)
        books_result = await db.execute(books_query)
        books = books_result.scalars().all()
        
        if books:
            # Soft delete - deactivate instead
            entity.is_active = False
        else:
            # Hard delete
            await db.delete(entity)
        
        await db.commit()
        return {"message": "Legal entity deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete legal entity: {str(e)}")