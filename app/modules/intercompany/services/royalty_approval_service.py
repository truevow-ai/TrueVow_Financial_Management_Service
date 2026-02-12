"""
Royalty Run Approval Workflow Service
Handles state machine transitions for royalty run approvals
"""
from typing import Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.modules.intercompany.models.royalty_model import RoyaltyCalculation, RoyaltyRunStatus
from app.modules.intercompany.repositories.royalty_repository import RoyaltyCalculationRepository
from app.modules.core.models.approval_policy_model import ApprovalObjectType
from app.modules.core.repositories.approval_policy_repository import ApprovalPolicyRepository
from app.modules.core.services.sod_validator import check_sod_for_royalty_run, SoDValidationError
from app.modules.core.models.audit_log_model import AuditLog
from app.core.logging import logger


class RoyaltyApprovalError(Exception):
    """Raised when approval workflow rules are violated"""
    pass


class RoyaltyApprovalService:
    """Service for royalty run approval workflows"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.royalty_repo = RoyaltyCalculationRepository(session)
        self.policy_repo = ApprovalPolicyRepository(session)
    
    async def submit_for_approval(
        self,
        run_id: UUID,
        user_id: UUID,
        user_role: str,
        reason: Optional[str] = None,
        row_version: Optional[int] = None
    ) -> RoyaltyCalculation:
        """
        Submit royalty run for approval.
        
        Transitions: DRAFT -> PENDING_APPROVAL
        """
        run = await self.royalty_repo.get_by_id(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Royalty run not found")
        
        # Check row_version for optimistic locking
        from app.core.row_version import check_row_version
        check_row_version(run.row_version, row_version, "royalty run")
        
        if run.status != RoyaltyRunStatus.DRAFT:
            raise RoyaltyApprovalError(
                f"Cannot submit royalty run in status {run.status.value}. "
                "Must be DRAFT."
            )
        
        # Get entity ID from agreement
        entity_id = run.agreement.from_entity_id
        
        # Check if approval is required
        approval_required = await self.policy_repo.is_approval_required(
            entity_id,
            ApprovalObjectType.ROYALTY_RUN
        )
        
        if not approval_required:
            # Skip approval, allow direct posting
            run.status = RoyaltyRunStatus.APPROVED
            run.approved_by = user_id
            run.approved_at = datetime.utcnow()
            run.decision_reason = reason
        else:
            # Submit for approval
            run.status = RoyaltyRunStatus.PENDING_APPROVAL
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
            action="ROYALTY_SUBMIT",
            object_id=run_id,
            before_status=RoyaltyRunStatus.DRAFT.value,
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
    ) -> RoyaltyCalculation:
        """
        Approve royalty run.
        
        Transitions: PENDING_APPROVAL -> APPROVED
        """
        run = await self.royalty_repo.get_by_id(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Royalty run not found")
        
        # Check row_version for optimistic locking
        from app.core.row_version import check_row_version
        check_row_version(run.row_version, row_version, "royalty run")
        
        if run.status != RoyaltyRunStatus.PENDING_APPROVAL:
            raise RoyaltyApprovalError(
                f"Cannot approve royalty run in status {run.status.value}. "
                "Must be PENDING_APPROVAL."
            )
        
        # Check SoD
        try:
            check_sod_for_royalty_run(
                user_id=user_id,
                user_role=user_role,
                run_submitted_by=run.submitted_by,
                run_approved_by=run.approved_by,
                run_posted_by=run.posted_by,
                action="approve",
                override_reason=override_reason
            )
        except SoDValidationError as e:
            raise RoyaltyApprovalError(str(e))
        
        # Approve
        run.status = RoyaltyRunStatus.APPROVED
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
            action="ROYALTY_APPROVE",
            object_id=run_id,
            before_status=RoyaltyRunStatus.PENDING_APPROVAL.value,
            after_status=RoyaltyRunStatus.APPROVED.value,
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
    ) -> RoyaltyCalculation:
        """
        Reject royalty run.
        
        Transitions: PENDING_APPROVAL -> REJECTED
        """
        if not reason or not reason.strip():
            raise RoyaltyApprovalError("Rejection reason is required")
        
        run = await self.royalty_repo.get_by_id(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Royalty run not found")
        
        # Check row_version for optimistic locking
        from app.core.row_version import check_row_version
        check_row_version(run.row_version, row_version, "royalty run")
        
        if run.status != RoyaltyRunStatus.PENDING_APPROVAL:
            raise RoyaltyApprovalError(
                f"Cannot reject royalty run in status {run.status.value}. "
                "Must be PENDING_APPROVAL."
            )
        
        # Check SoD
        try:
            check_sod_for_royalty_run(
                user_id=user_id,
                user_role=user_role,
                run_submitted_by=run.submitted_by,
                run_approved_by=run.approved_by,
                run_posted_by=run.posted_by,
                action="approve",
                override_reason=None
            )
        except SoDValidationError as e:
            raise RoyaltyApprovalError(str(e))
        
        # Reject
        run.status = RoyaltyRunStatus.REJECTED
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
            action="ROYALTY_REJECT",
            object_id=run_id,
            before_status=RoyaltyRunStatus.PENDING_APPROVAL.value,
            after_status=RoyaltyRunStatus.REJECTED.value,
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
            object_type="royalty_calculation",
            object_id=object_id,
            before_json={"status": before_status},
            after_json={"status": after_status},
            reason=reason
        )
        self.session.add(audit_log)
