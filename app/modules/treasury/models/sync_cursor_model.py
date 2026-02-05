"""Sync Cursor Model"""
from sqlalchemy import Column, String, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.shared.models.base_model import BaseModel


class SyncCursor(BaseModel):
    """Sync cursor for external system integration"""
    __tablename__ = "treasury_import_cursor"
    
    legal_entity_id = Column(UUID(as_uuid=True), ForeignKey("legal_entity.id"), nullable=False, index=True)
    source_system = Column(String(50), nullable=False, index=True)  # billing, treasury, etc.
    object_type = Column(String(50), nullable=False)  # transaction, settlement, etc.
    cursor_value = Column(String(255), nullable=False)  # Last processed ID/timestamp
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    entity = relationship("LegalEntity")
    
    __table_args__ = (
        UniqueConstraint("legal_entity_id", "source_system", "object_type", name="uq_treasury_import_cursor_entity_src_type"),
        {"comment": "Sync cursors for replay-safe external integration"},
    )
    
    def __repr__(self):
        return f"<SyncCursor(source={self.source_system}, type={self.object_type}, cursor={self.cursor_value})>"
