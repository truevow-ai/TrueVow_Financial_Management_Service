"""
Period Close Approval Workflow Service
Handles state machine transitions for period close approvals
"""
from typing import Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.modules.general_ledger.models.accounting_period_model import AccountingPeriod, PeriodStatus
from app.modules.general_ledger.repositories.accounting_period_repository import AccountingPeriodRepository
from app.modules.general_ledger.models.period_close_checklist_model import (
    PeriodCloseChecklist,
    ChecklistItemCode,
    ChecklistItemStatus
)
from app.modules.core.models.approval_policy_model import ApprovalObjectType
from app.modules.core.repositories.approval_policy_repository import ApprovalPolicyRepository
from app.modules.core.services.sod_validator import check_sod_for_period_close, SoDValidationError
from app.modules.core.models.audit_log_model import AuditLog
from app.core.logging import logger


class PeriodCloseApprovalError(Exception):
    """Raised when approval workflow rules are violated"""
    pass


class PeriodCloseApprovalService:
    """Service for period close approval workflows"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.period_repo = AccountingPeriodRepository(session)
        self.policy_repo = ApprovalPolicyRepository(session)
    
    async def submit_close(
        self,
        period_id: UUID,
        user_id: UUID,
        user_role: str,
        reason: Optional[str] = None,
        row_version: Optional[int] = None
    ) -> AccountingPeriod:
        """Submit period for close approval. Transitions: SOFT_CLOSED -> PENDING_CLOSE_APPROVAL"""
        period = await self.period_repo.get_by_id(period_id)
        if not period:
            raise HTTPException(status_code=404, detail="Period not found")
        
        # Check row_version for optimistic locking
        from app.core.row_version import check_row_version
        check_row_version(period.row_version, row_version, "accounting period")
        
        if period.status not in (PeriodStatus.OPEN, PeriodStatus.SOFT_CLOSED):
            raise PeriodCloseApprovalError(
                f"Cannot submit period for close in status {period.status.value}. Must be OPEN or SOFT_CLOSED."
            )
        
        checklist_complete = await self._check_checklist_complete(period_id)
        if not checklist_complete:
            raise PeriodCloseApprovalError(
                "Cannot submit period for close. Close checklist items are not complete."
            )
        
        # Get entity ID from book
        from app.modules.general_ledger.models.book_model import Book
        book_stmt = select(Book).where(Book.id == period.book_id)
        book_result = await self.session.execute(book_stmt)
        book = book_result.scalar_one_or_none()
        entity_id = book.legal_entity_id if book else None
        
        if not entity_id:
            raise PeriodCloseApprovalError("Cannot determine entity for period")
        
        approval_required = await self.policy_repo.is_approval_required(
            entity_id,
            ApprovalObjectType.PERIOD_CLOSE
        )
        
        if not approval_required:
            period.status = PeriodStatus.CLOSED
            period.approved_by = user_id
            period.approved_at = datetime.utcnow()
            period.decision_reason = reason
        else:
            if period.status == PeriodStatus.OPEN:
                period.status = PeriodStatus.SOFT_CLOSED
            period.status = PeriodStatus.PENDING_CLOSE_APPROVAL
            period.submitted_by = user_id
            period.submitted_at = datetime.utcnow()
            period.decision_reason = reason
        
        period.row_version += 1
        period.updated_by = user_id
        await self.session.commit()
        
        await self._log_audit(
            user_id=user_id,
            user_role=user_role,
            action="PERIOD_CLOSE_SUBMIT",
            object_id=period_id,
            before_status=period.status.value,
            after_status=PeriodStatus.PENDING_CLOSE_APPROVAL.value,
            reason=reason
        )
        
        return period
    
    async def approve_close(
        self,
        period_id: UUID,
        user_id: UUID,
        user_role: str,
        reason: Optional[str] = None,
        override_reason: Optional[str] = None,
        row_version: Optional[int] = None
    ) -> AccountingPeriod:
        """Approve period close. Transitions: PENDING_CLOSE_APPROVAL -> CLOSED"""
        period = await self.period_repo.get_by_id(period_id)
        if not period:
            raise HTTPException(status_code=404, detail="Period not found")
        
        # Check row_version for optimistic locking
        from app.core.row_version import check_row_version
        check_row_version(period.row_version, row_version, "accounting period")
        
        if period.status != PeriodStatus.PENDING_CLOSE_APPROVAL:
            raise PeriodCloseApprovalError(
                f"Cannot approve period close in status {period.status.value}. Must be PENDING_CLOSE_APPROVAL."
            )
        
        try:
            check_sod_for_period_close(
                user_id=user_id,
                user_role=user_role,
                period_submitted_by=period.submitted_by,
                period_approved_by=period.approved_by,
                action="approve",
                override_reason=override_reason
            )
        except SoDValidationError as e:
            raise PeriodCloseApprovalError(str(e))
        
        period.status = PeriodStatus.CLOSED
        period.approved_by = user_id
        period.approved_at = datetime.utcnow()
        period.closed_by = user_id
        period.closed_at = datetime.utcnow()
        period.decision_reason = reason
        period.row_version += 1
        period.updated_by = user_id
        await self.session.commit()
        
        await self._log_audit(
            user_id=user_id,
            user_role=user_role,
            action="PERIOD_CLOSE_APPROVE",
            object_id=period_id,
            before_status=PeriodStatus.PENDING_CLOSE_APPROVAL.value,
            after_status=PeriodStatus.CLOSED.value,
            reason=reason or override_reason
        )
        
        return period
    
    async def _check_checklist_complete(self, period_id: UUID) -> bool:
        """Check if all close checklist items are complete"""
        stmt = select(PeriodCloseChecklist).where(
            PeriodCloseChecklist.period_id == period_id
        )
        result = await self.session.execute(stmt)
        items = result.scalars().all()
        
        if not items:
            return False
        
        for item in items:
            if item.status != ChecklistItemStatus.COMPLETE:
                return False
        
        return True
    
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
            object_type="accounting_period",
            object_id=object_id,
            before_json={"status": before_status},
            after_json={"status": after_status},
            reason=reason
        )
        self.session.add(audit_log)
