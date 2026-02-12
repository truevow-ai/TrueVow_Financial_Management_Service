"""
Segregation of Duties (SoD) validation for approval workflows.
Stub implementations allow app to load; replace with real SoD rules when required.
"""
from typing import Any, Optional
from uuid import UUID


class SoDValidationError(Exception):
    """Raised when a requested action violates SoD rules."""
    pass


def check_sod_for_period_close(
    user_id: UUID,
    user_role: str,
    period_submitted_by: Optional[UUID],
    period_approved_by: Optional[UUID],
    action: str,
    override_reason: Optional[str] = None,
    **kwargs: Any,
) -> None:
    """Validate SoD for period close approve/reject. Stub: no-op."""
    pass


def check_sod_for_royalty_run(
    user_id: UUID,
    user_role: str,
    run_submitted_by: Optional[UUID],
    run_approved_by: Optional[UUID],
    run_posted_by: Optional[UUID],
    action: str,
    override_reason: Optional[str] = None,
    **kwargs: Any,
) -> None:
    """Validate SoD for royalty run approve/reject. Stub: no-op."""
    pass


def check_sod_for_reconciliation_adjustment(
    user_id: UUID,
    user_role: str,
    batch_submitted_by: Optional[UUID],
    batch_approved_by: Optional[UUID],
    batch_posted_by: Optional[UUID],
    action: str,
    override_reason: Optional[str] = None,
    **kwargs: Any,
) -> None:
    """Validate SoD for reconciliation adjustment approve/reject. Stub: no-op."""
    pass


def check_sod_for_ap_bill(
    submitted_by: Optional[UUID],
    approved_by: Optional[UUID],
    user_role: str,
    override_reason: Optional[str] = None,
    **kwargs: Any,
) -> None:
    """Validate SoD for AP bill approve/reject. Stub: no-op."""
    pass


def check_sod_for_payroll(
    user_id: UUID,
    user_role: str,
    payroll_run_submitted_by: Optional[UUID],
    payroll_run_approved_by: Optional[UUID],
    payroll_run_posted_by: Optional[UUID],
    action: str,
    override_reason: Optional[str] = None,
    **kwargs: Any,
) -> None:
    """Validate SoD for payroll run approve/reject. Stub: no-op."""
    pass
