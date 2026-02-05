"""
Reconciliation Approval Workflow Service
Handles state machine transitions for reconciliation adjustment batch approvals
"""
from typing import Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.modules.general_ledger.models.reconciliation_adjustment_batch_model import (
    ReconciliationAdjustmentBatch,
    AdjustmentBatchStatus
)
from app.modules.general_ledger.repositories.reconciliation_adjustment_batch_repository import (
    ReconciliationAdjustmentBatchRepository
)
from app.modules.core.models.approval_policy_model import ApprovalObjectType
from app.modules.core.repositories.approval_policy_repository import ApprovalPolicyRepository
from app.modules.core.services.sod_validator import check_sod_for_reconciliation_adjustment, SoDValidationError
from app.modules.core.models.audit_log_model import AuditLog
from app.core.logging import logger


class ReconciliationApprovalError(Exception):
    """Raised when approval workflow rules are violated"""
    pass


class ReconciliationApprovalService:
    """Service for reconciliation adjustment batch approval workflows"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.batch_repo = ReconciliationAdjustmentBatchRepository(session)
        self.policy_repo = ApprovalPolicyRepository(session)
    
    async def submit_for_approval(
        self,
        batch_id: UUID,
        user_id: UUID,
        user_role: str,
        reason: Optional[str] = None,
        row_version: Optional[int] = None
    ) -> ReconciliationAdjustmentBatch:
        """
        Submit reconciliation adjustment batch for approval.
        
        Transitions: DRAFT -> PENDING_APPROVAL
        """
        batch = await self.batch_repo.get_by_id(batch_id)
        if not batch:
            raise HTTPException(status_code=404, detail="Reconciliation adjustment batch not found")
        
        # Check row_version for optimistic locking
        from app.core.row_version import check_row_version
        check_row_version(batch.row_version, row_version, "reconciliation adjustment batch")
        
        if batch.status != AdjustmentBatchStatus.DRAFT:
            raise ReconciliationApprovalError(
                f"Cannot submit adjustment batch in status {batch.status.value}. "
                "Must be DRAFT."
            )
        
        # Check if approval is required
        approval_required = await self.policy_repo.is_approval_required(
            batch.legal_entity_id,
            ApprovalObjectType.RECONCILIATION_ADJUSTMENT
        )
        
        if not approval_required:
            # Skip approval, allow direct posting
            batch.status = AdjustmentBatchStatus.APPROVED
            batch.approved_by = user_id
            batch.approved_at = datetime.utcnow()
            batch.decision_reason = reason
        else:
            # Submit for approval
            batch.status = AdjustmentBatchStatus.PENDING_APPROVAL
            batch.submitted_by = user_id
            batch.submitted_at = datetime.utcnow()
            batch.decision_reason = reason
        
        batch.row_version += 1
        
        await self.session.commit()
        
        # Audit log
        await self._log_audit(
            user_id=user_id,
            user_role=user_role,
            action="RECONCILIATION_ADJUSTMENT_SUBMIT",
            object_id=batch_id,
            before_status=AdjustmentBatchStatus.DRAFT.value,
            after_status=batch.status.value,
            reason=reason
        )
        
        return batch
    
    async def approve(
        self,
        batch_id: UUID,
        user_id: UUID,
        user_role: str,
        reason: Optional[str] = None,
        override_reason: Optional[str] = None,
        row_version: Optional[int] = None
    ) -> ReconciliationAdjustmentBatch:
        """
        Approve reconciliation adjustment batch.
        
        Transitions: PENDING_APPROVAL -> APPROVED
        """
        batch = await self.batch_repo.get_by_id(batch_id)
        if not batch:
            raise HTTPException(status_code=404, detail="Reconciliation adjustment batch not found")
        
        # Check row_version for optimistic locking
        from app.core.row_version import check_row_version
        check_row_version(batch.row_version, row_version, "reconciliation adjustment batch")
        
        if batch.status != AdjustmentBatchStatus.PENDING_APPROVAL:
            raise ReconciliationApprovalError(
                f"Cannot approve adjustment batch in status {batch.status.value}. "
                "Must be PENDING_APPROVAL."
            )
        
        # Check SoD
        try:
            check_sod_for_reconciliation_adjustment(
                user_id=user_id,
                user_role=user_role,
                batch_submitted_by=batch.submitted_by,
                batch_approved_by=batch.approved_by,
                batch_posted_by=batch.posted_by,
                action="approve",
                override_reason=override_reason
            )
        except SoDValidationError as e:
            raise ReconciliationApprovalError(str(e))
        
        # Approve
        batch.status = AdjustmentBatchStatus.APPROVED
        batch.approved_by = user_id
        batch.approved_at = datetime.utcnow()
        batch.decision_reason = reason
        batch.row_version += 1
        
        await self.session.commit()
        
        # Audit log
        await self._log_audit(
            user_id=user_id,
            user_role=user_role,
            action="RECONCILIATION_ADJUSTMENT_APPROVE",
            object_id=batch_id,
            before_status=AdjustmentBatchStatus.PENDING_APPROVAL.value,
            after_status=AdjustmentBatchStatus.APPROVED.value,
            reason=reason or override_reason
        )
        
        return batch
    
    async def reject(
        self,
        batch_id: UUID,
        user_id: UUID,
        user_role: str,
        reason: str,  # Required for rejection
        row_version: Optional[int] = None
    ) -> ReconciliationAdjustmentBatch:
        """
        Reject reconciliation adjustment batch.
        
        Transitions: PENDING_APPROVAL -> REJECTED
        """
        if not reason or not reason.strip():
            raise ReconciliationApprovalError("Rejection reason is required")
        
        batch = await self.batch_repo.get_by_id(batch_id)
        if not batch:
            raise HTTPException(status_code=404, detail="Reconciliation adjustment batch not found")
        
        # Check row_version for optimistic locking
        from app.core.row_version import check_row_version
        check_row_version(batch.row_version, row_version, "reconciliation adjustment batch")
        
        if batch.status != AdjustmentBatchStatus.PENDING_APPROVAL:
            raise ReconciliationApprovalError(
                f"Cannot reject adjustment batch in status {batch.status.value}. "
                "Must be PENDING_APPROVAL."
            )
        
        # Check SoD
        try:
            check_sod_for_reconciliation_adjustment(
                user_id=user_id,
                user_role=user_role,
                batch_submitted_by=batch.submitted_by,
                batch_approved_by=batch.approved_by,
                batch_posted_by=batch.posted_by,
                action="approve",  # Reject uses same SoD check as approve
                override_reason=None
            )
        except SoDValidationError as e:
            raise ReconciliationApprovalError(str(e))
        
        # Reject
        batch.status = AdjustmentBatchStatus.REJECTED
        batch.rejected_by = user_id
        batch.rejected_at = datetime.utcnow()
        batch.decision_reason = reason
        batch.row_version += 1
        
        await self.session.commit()
        
        # Audit log
        await self._log_audit(
            user_id=user_id,
            user_role=user_role,
            action="RECONCILIATION_ADJUSTMENT_REJECT",
            object_id=batch_id,
            before_status=AdjustmentBatchStatus.PENDING_APPROVAL.value,
            after_status=AdjustmentBatchStatus.REJECTED.value,
            reason=reason
        )
        
        return batch
    
    async def _log_audit(
        self,
        user_id: UUID,
        user_role: str,
        action: str,
        object_id: UUID,
        before_status: str,
        after_status: str,
        reason: Optional[str] = None
    ):
        """Log approval action to audit log"""
        audit_log = AuditLog(
            actor_user_id=user_id,
            actor_role=user_role,
            action=action,
            object_type="reconciliation_adjustment_batch",
            object_id=object_id,
            before_json={"status": before_status},
            after_json={"status": after_status},
            reason=reason
        )
        self.session.add(audit_log)
        # Note: Don't commit here, let caller commit
