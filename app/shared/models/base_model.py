"""Base model class with common fields"""
from sqlalchemy import Column, DateTime, func, Index, Integer
from sqlalchemy.dialects.postgresql import UUID
from typing import Optional
import uuid
from app.core.db_metadata import Base


class BaseModel(Base):
    """Base model with common fields including full lifecycle audit trail and optimistic locking."""
    __abstract__ = True
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Lifecycle audit - creation
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by = Column(UUID(as_uuid=True), nullable=True)  # User ID from JWT/Clerk
    
    # Lifecycle audit - updates
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    updated_by = Column(UUID(as_uuid=True), nullable=True)  # User ID from JWT/Clerk
    
    # Lifecycle audit - soft delete
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)  # When soft-deleted
    deleted_by = Column(UUID(as_uuid=True), nullable=True)  # Who soft-deleted it
    
    # Optimistic locking - protect against concurrent updates
    row_version = Column(Integer, default=1, nullable=False)
    
    def soft_delete(self, deleted_by_user_id: Optional[uuid.UUID] = None) -> None:
        """
        Mark this record as soft-deleted.
        
        Writes to deleted_at and deleted_by, NOT to updated_by.
        
        Args:
            deleted_by_user_id: User ID performing the deletion
        """
        from datetime import datetime, timezone
        self.deleted_at = datetime.now(timezone.utc)
        self.deleted_by = deleted_by_user_id
    
    def is_deleted(self) -> bool:
        """Check if this record has been soft-deleted."""
        return self.deleted_at is not None
    
    def restore(self) -> None:
        """Restore a soft-deleted record."""
        self.deleted_at = None
        self.deleted_by = None
    
    def increment_version(self) -> None:
        """Increment row version for optimistic locking. Call before any update."""
        self.row_version = (self.row_version or 0) + 1
