"""External Sync Models"""
from sqlalchemy import Column, String, ForeignKey, DateTime, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.shared.models.base_model import BaseModel


class ExternalSyncCursor(BaseModel):
    """External sync cursor for replay-safe integration"""
    __tablename__ = "external_sync_cursor"
    
    legal_entity_id = Column(UUID(as_uuid=True), ForeignKey("legal_entity.id"), nullable=False, index=True)
    source_service = Column(String(50), nullable=False, index=True)  # billing, treasury, etc.
    object_type = Column(String(50), nullable=False)  # customer, invoice, payment, etc.
    cursor_value = Column(String(255), nullable=False)  # Last processed ID/timestamp
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    entity = relationship("LegalEntity")
    
    __table_args__ = (
        UniqueConstraint("legal_entity_id", "source_service", "object_type", name="uq_external_sync_cursor_entity_src_type"),
        {"comment": "Sync cursors for replay-safe external integration"},
    )
    
    def __repr__(self):
        return f"<ExternalSyncCursor(source={self.source_service}, type={self.object_type}, cursor={self.cursor_value})>"


class SourceObjectMap(BaseModel):
    """Mapping of external IDs to internal IDs"""
    __tablename__ = "source_object_map"
    
    legal_entity_id = Column(UUID(as_uuid=True), ForeignKey("legal_entity.id"), nullable=False, index=True)
    source_service = Column(String(50), nullable=False, index=True)  # billing, treasury, etc.
    object_type = Column(String(50), nullable=False)  # customer, invoice, payment, etc.
    external_id = Column(String(255), nullable=False, index=True)  # External system ID
    internal_id = Column(UUID(as_uuid=True), nullable=False)  # Internal FM ID
    book_id = Column(UUID(as_uuid=True), ForeignKey("book.id"), nullable=True)  # Optional book context
    
    # Relationships
    entity = relationship("LegalEntity")
    book = relationship("Book")
    
    __table_args__ = (
        UniqueConstraint("legal_entity_id", "source_service", "object_type", "external_id", name="uq_source_object_map_entity_src_type_ext"),
        {"comment": "Mapping of external IDs to internal IDs for deduplication"},
    )
    
    def __repr__(self):
        return f"<SourceObjectMap(source={self.source_service}, type={self.object_type}, external={self.external_id}, internal={self.internal_id})>"
