"""Approval Policy Model"""
from sqlalchemy import Column, String, Boolean, ForeignKey, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import enum
from app.shared.models.base_model import BaseModel


class ApprovalObjectType(str, enum.Enum):
    """Types of objects that can require approval"""
    PAYROLL_RUN = "PAYROLL_RUN"
    REC_ADJUSTMENT_BATCH = "REC_ADJUSTMENT_BATCH"
    PERIOD_CLOSE = "PERIOD_CLOSE"
    ROYALTY_RUN = "ROYALTY_RUN"
    AP_BILL = "AP_BILL"


class ApprovalPolicy(BaseModel):
    """Approval policy configuration per entity and object type"""
    __tablename__ = "approval_policy"
    
    legal_entity_id = Column(UUID(as_uuid=True), ForeignKey("legal_entity.id"), nullable=False, index=True)
    object_type = Column(SQLEnum(ApprovalObjectType), nullable=False, index=True)
    approval_required = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    entity = relationship("LegalEntity", backref="approval_policies")
    
    __table_args__ = (
        UniqueConstraint("legal_entity_id", "object_type", name="uq_approval_policy_entity_type"),
        {"comment": "Approval policy configuration - allows disabling approvals per entity"},
    )
    
    def __repr__(self):
        return f"<ApprovalPolicy(entity={self.legal_entity_id}, object_type={self.object_type.value}, required={self.approval_required})>"
