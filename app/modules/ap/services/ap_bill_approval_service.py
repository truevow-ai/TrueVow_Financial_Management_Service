"""
AP Bill Approval Workflow Service
Handles state machine transitions for AP bill approvals
"""
from typing import Optional
from uuid import UUID
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.modules.ap.models.ap_bill_model import APBill, BillStatus
from app.modules.ap.repositories.ap_bill_repository import APBillRepository
from app.modules.core.models.approval_policy_model import ApprovalObjectType
from app.modules.core.repositories.approval_policy_repository import ApprovalPolicyRepository
from app.modules.core.services.sod_validator import check_sod_for_ap_bill, SoDValidationError
from app.modules.core.models.audit_log_model import AuditLog
from app.core.logging import logger


class APBillApprovalError(Exception):
    """Raised when approval workflow rules are violated"""
    pass


class APBillApprovalService:
    """Service for AP bill approval workflows"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.bill_repo = APBillRepository(session)
        self.policy_repo = ApprovalPolicyRepository(session)
    
    async def submit_for_approval(
        self,
        bill_id: UUID,
        user_id: UUID,
        user_role: str,
        reason: Optional[str] = None,
        row_version: Optional[int] = None
    ) -> APBill:
        """
        Submit AP bill for approval.
        
        Transitions: DRAFT -> PENDING_APPROVAL
        """
        bill = await self.bill_repo.get_by_id(bill_id)
        if not bill:
            raise HTTPException(status_code=404, detail="AP bill not found")
        
        # Check row_version for optimistic locking
        from app.core.row_version import check_row_version
        check_row_version(bill.row_version, row_version, "AP bill")
        
        if bill.status != BillStatus.DRAFT:
            raise APBillApprovalError(
                f"Cannot submit AP bill in status {bill.status.value}. "
                "Must be DRAFT."
            )
        
        # Check if approval is required
        approval_required = await self.policy_repo.is_approval_required(
            bill.legal_entity_id,
            ApprovalObjectType.AP_BILL
        )
        
        if not approval_required:
            # Skip approval, allow direct posting
            bill.status = BillStatus.APPROVED
            bill.approved_by = user_id
            bill.approved_at = date.today()
            bill.decision_reason = reason
        else:
            # Submit for approval
            bill.status = BillStatus.PENDING_APPROVAL
            bill.submitted_by = user_id
            bill.submitted_at = date.today()
            bill.decision_reason = reason
        
        bill.row_version += 1
        bill.updated_by = user_id
        
        await self.session.commit()
        
        # Audit log
        await self._log_audit(
            bill_id=bill_id,
            action="SUBMIT_FOR_APPROVAL",
            user_id=user_id,
            user_role=user_role,
            reason=reason
        )
        
        return bill
    
    async def approve(
        self,
        bill_id: UUID,
        user_id: UUID,
        user_role: str,
        reason: Optional[str] = None,
        override_reason: Optional[str] = None,
        row_version: Optional[int] = None
    ) -> APBill:
        """
        Approve AP bill.
        
        Transitions: PENDING_APPROVAL -> APPROVED
        """
        bill = await self.bill_repo.get_by_id(bill_id)
        if not bill:
            raise HTTPException(status_code=404, detail="AP bill not found")
        
        # Check row_version for optimistic locking
        from app.core.row_version import check_row_version
        check_row_version(bill.row_version, row_version, "AP bill")
        
        if bill.status != BillStatus.PENDING_APPROVAL:
            raise APBillApprovalError(
                f"Cannot approve AP bill in status {bill.status.value}. "
                "Must be PENDING_APPROVAL."
            )
        
        # Check SoD (Separation of Duties)
        try:
            check_sod_for_ap_bill(
                submitted_by=bill.submitted_by,
                approved_by=user_id,
                user_role=user_role,
                override_reason=override_reason
            )
        except SoDValidationError as e:
            raise APBillApprovalError(str(e))
        
        bill.status = BillStatus.APPROVED
        bill.approved_by = user_id
        bill.approved_at = date.today()
        bill.decision_reason = reason
        bill.row_version += 1
        bill.updated_by = user_id
        
        await self.session.commit()
        
        # Audit log
        await self._log_audit(
            bill_id=bill_id,
            action="APPROVE",
            user_id=user_id,
            user_role=user_role,
            reason=reason,
            override_reason=override_reason
        )
        
        return bill
    
    async def reject(
        self,
        bill_id: UUID,
        user_id: UUID,
        user_role: str,
        reason: str,  # Required for rejection
        row_version: Optional[int] = None
    ) -> APBill:
        """
        Reject AP bill.
        
        Transitions: PENDING_APPROVAL -> REJECTED
        """
        if not reason or not reason.strip():
            raise APBillApprovalError("Rejection reason is required")
        
        bill = await self.bill_repo.get_by_id(bill_id)
        if not bill:
            raise HTTPException(status_code=404, detail="AP bill not found")
        
        # Check row_version for optimistic locking
        from app.core.row_version import check_row_version
        check_row_version(bill.row_version, row_version, "AP bill")
        
        if bill.status != BillStatus.PENDING_APPROVAL:
            raise APBillApprovalError(
                f"Cannot reject AP bill in status {bill.status.value}. "
                "Must be PENDING_APPROVAL."
            )
        
        bill.status = BillStatus.REJECTED
        bill.rejected_by = user_id
        bill.rejected_at = date.today()
        bill.decision_reason = reason
        bill.row_version += 1
        bill.updated_by = user_id
        
        await self.session.commit()
        
        # Audit log
        await self._log_audit(
            bill_id=bill_id,
            action="REJECT",
            user_id=user_id,
            user_role=user_role,
            reason=reason
        )
        
        return bill
    
    async def _log_audit(
        self,
        bill_id: UUID,
        action: str,
        user_id: UUID,
        user_role: str,
        reason: Optional[str] = None,
        override_reason: Optional[str] = None
    ):
        """Log approval action to audit log"""
        audit = AuditLog(
            entity_type="AP_BILL",
            entity_id=bill_id,
            action=action,
            actor_user_id=user_id,
            actor_role=user_role,
            details={
                "reason": reason,
                "override_reason": override_reason
            }
        )
        self.session.add(audit)
        await self.session.flush()
