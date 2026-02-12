"""Idempotency Key Model"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import func
import uuid
import enum
from app.core.db_metadata import Base


class IdempotencyState(str, enum.Enum):
    """Idempotency record state"""
    PENDING = "PENDING"  # Key reserved, handler executing
    COMPLETED = "COMPLETED"  # Handler completed, response stored
    FAILED = "FAILED"  # Handler failed, error response stored


class IdempotencyKey(Base):
    """Idempotency key model for write API idempotency"""
    __tablename__ = "idempotency_keys"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Scope fields (included in uniqueness)
    legal_entity_id = Column(UUID(as_uuid=True), ForeignKey("legal_entity.id"), nullable=False, index=True)
    book_id = Column(UUID(as_uuid=True), ForeignKey("book.id"), nullable=False, index=True)  # NOT NULL - all MVP endpoints have book_id
    endpoint_key = Column(String(255), nullable=False, index=True)  # Hardcoded endpoint constant (e.g., "JE_POST")
    idempotency_key = Column(String(255), nullable=False, index=True)  # Idempotency-Key header value
    
    # Request/Response tracking
    request_hash = Column(String(64), nullable=False)  # Hash of request body (canonical JSON)
    state = Column(SQLEnum(IdempotencyState), default=IdempotencyState.PENDING, nullable=False, index=True)  # PENDING -> COMPLETED/FAILED
    response_status = Column(Integer, nullable=True)  # HTTP status code (NULL for PENDING)
    response_blob = Column(Text, nullable=True)  # Stored response (JSON, NULL for PENDING)
    
    # Metadata for correlation/audit (e.g., batch_id for sync operations)
    metadata_json = Column(Text, nullable=True)  # JSON blob for correlation data (batch_id, cursor_start, cursor_end, etc.)
    
    # Locking (for race condition prevention)
    locked_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)  # When PENDING state was set
    
    # Audit (not in uniqueness)
    actor_user_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # For audit/trace only
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    __table_args__ = (
        UniqueConstraint("legal_entity_id", "book_id", "endpoint_key", "idempotency_key", name="uq_idempotency_entity_book_endpoint_key"),
        {"comment": "Idempotency keys for write API idempotency - scoped by entity, book, endpoint"},
    )
    
    def __repr__(self):
        return f"<IdempotencyKey(entity={self.legal_entity_id}, book={self.book_id}, endpoint={self.endpoint_key}, key={self.idempotency_key})>"
