"""
Payroll Approval Workflow Service
Handles state machine transitions for payroll run approvals
"""
from typing import Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.modules.payroll.models.payroll_run_model import PayrollRun, PayrollRunStatus
from app.modules.payroll.repositories.payroll_run_repository import PayrollRunRepository
from app.modules.core.models.approval_policy_model import ApprovalObjectType
from app.modules.core.repositories.approval_policy_repository import ApprovalPolicyRepository
from app.modules.core.services.sod_validator import check_sod_for_payroll, SoDValidationError
from app.modules.core.models.audit_log_model import AuditLog
from app.core.logging import logger


class PayrollApprovalError(Exception):
    """Raised when approval workflow rules are violated"""
    pass


class PayrollApprovalService:
    """Service for payroll run approval workflows"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.run_repo = PayrollRunRepository(session)
        self.policy_repo = ApprovalPolicyRepository(session)
    
    async def submit_for_approval(
        self,
        run_id: UUID,
        user_id: UUID,
        user_role: str,
        reason: Optional[str] = None,
        row_version: Optional[int] = None
    ) -> PayrollRun:
        """
        Submit payroll run for approval.
        
        Transitions: CALCULATED -> PENDING_APPROVAL
        """
        run = await self.run_repo.get_by_id(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Payroll run not found")
        
        # Check row_version for optimistic locking
        from app.core.row_version import check_row_version
        check_row_version(run.row_version, row_version, "payroll run")
        
        if run.status != PayrollRunStatus.CALCULATED:
            raise PayrollApprovalError(
                f"Cannot submit payroll run in status {run.status.value}. "
                "Must be CALCULATED."
            )
        
        # Check if approval is required
        approval_required = await self.policy_repo.is_approval_required(
            run.legal_entity_id,
            ApprovalObjectType.PAYROLL_RUN
        )
        
        if not approval_required:
            # Skip approval, allow direct posting
            run.status = PayrollRunStatus.APPROVED
            run.approved_by = user_id
            run.approved_at = datetime.utcnow()
            run.decision_reason = reason
        else:
            # Submit for approval
            run.status = PayrollRunStatus.PENDING_APPROVAL
            run.submitted_by = user_id
            run.submitted_at = datetime.utcnow()
            run.decision_reason = reason
        
        run.row_version += 1
        run.updated_by = user_id
        
        await self.session.commit()
        
        # Audit log
        await self._log_audit(
            user_id=user_id,
            user_role=user_role,
            action="PAYROLL_SUBMIT",
            object_id=run_id,
            before_status=PayrollRunStatus.CALCULATED.value,
            after_status=run.status.value,
            reason=reason
        )
        
        return run
    
    async def approve(
        self,
        run_id: UUID,
        user_id: UUID,
        user_role: str,
        reason: Optional[str] = None,
        override_reason: Optional[str] = None,
        row_version: Optional[int] = None
    ) -> PayrollRun:
        """
        Approve payroll run.
        
        Transitions: PENDING_APPROVAL -> APPROVED
        """
        run = await self.run_repo.get_by_id(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Payroll run not found")
        
        # Check row_version for optimistic locking
        from app.core.row_version import check_row_version
        check_row_version(run.row_version, row_version, "payroll run")
        
        if run.status != PayrollRunStatus.PENDING_APPROVAL:
            raise PayrollApprovalError(
                f"Cannot approve payroll run in status {run.status.value}. "
                "Must be PENDING_APPROVAL."
            )
        
        # Check SoD
        try:
            check_sod_for_payroll(
                user_id=user_id,
                user_role=user_role,
                payroll_run_submitted_by=run.submitted_by,
                payroll_run_approved_by=run.approved_by,
                payroll_run_posted_by=run.posted_by,
                action="approve",
                override_reason=override_reason
            )
        except SoDValidationError as e:
            raise PayrollApprovalError(str(e))
        
        # Approve
        run.status = PayrollRunStatus.APPROVED
        run.approved_by = user_id
        run.approved_at = datetime.utcnow()
        run.decision_reason = reason
        run.row_version += 1
        run.updated_by = user_id
        
        await self.session.commit()
        
        # Audit log
        await self._log_audit(
            user_id=user_id,
            user_role=user_role,
            action="PAYROLL_APPROVE",
            object_id=run_id,
            before_status=PayrollRunStatus.PENDING_APPROVAL.value,
            after_status=PayrollRunStatus.APPROVED.value,
            reason=reason or override_reason
        )
        
        return run
    
    async def reject(
        self,
        run_id: UUID,
        user_id: UUID,
        user_role: str,
        reason: str,  # Required for rejection
        row_version: Optional[int] = None
    ) -> PayrollRun:
        """
        Reject payroll run.
        
        Transitions: PENDING_APPROVAL -> REJECTED
        """
        if not reason or not reason.strip():
            raise PayrollApprovalError("Rejection reason is required")
        
        run = await self.run_repo.get_by_id(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Payroll run not found")
        
        # Check row_version for optimistic locking
        from app.core.row_version import check_row_version
        check_row_version(run.row_version, row_version, "payroll run")
        
        if run.status != PayrollRunStatus.PENDING_APPROVAL:
            raise PayrollApprovalError(
                f"Cannot reject payroll run in status {run.status.value}. "
                "Must be PENDING_APPROVAL."
            )
        
        # Check SoD
        try:
            check_sod_for_payroll(
                user_id=user_id,
                user_role=user_role,
                payroll_run_submitted_by=run.submitted_by,
                payroll_run_approved_by=run.approved_by,
                payroll_run_posted_by=run.posted_by,
                action="approve",  # Reject uses same SoD check as approve
                override_reason=None
            )
        except SoDValidationError as e:
            raise PayrollApprovalError(str(e))
        
        # Reject
        run.status = PayrollRunStatus.REJECTED
        run.rejected_by = user_id
        run.rejected_at = datetime.utcnow()
        run.decision_reason = reason
        run.row_version += 1
        run.updated_by = user_id
        
        await self.session.commit()
        
        # Audit log
        await self._log_audit(
            user_id=user_id,
            user_role=user_role,
            action="PAYROLL_REJECT",
            object_id=run_id,
            before_status=PayrollRunStatus.PENDING_APPROVAL.value,
            after_status=PayrollRunStatus.REJECTED.value,
            reason=reason
        )
        
        return run
    
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
            object_type="payroll_run",
            object_id=object_id,
            before_json={"status": before_status},
            after_json={"status": after_status},
            reason=reason
        )
        self.session.add(audit_log)
        # Note: Don't commit here, let caller commit
