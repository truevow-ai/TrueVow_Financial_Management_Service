"""
Row Version Conflict Checking Utilities
"""
from typing import Optional
from fastapi import HTTPException, status


def check_row_version(
    current_version: int,
    provided_version: Optional[int],
    object_name: str = "object"
) -> None:
    """
    Check row version and raise 409 Conflict if mismatch.
    
    Args:
        current_version: The current row_version from database
        provided_version: The row_version provided in request (None if not provided)
        object_name: Name of object for error message (e.g., "payroll run")
    
    Raises:
        HTTPException(409) if versions don't match
    """
    if provided_version is not None and current_version != provided_version:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Row version mismatch for {object_name}. "
                   f"Expected {current_version}, got {provided_version}. "
                   "Please refresh and try again."
        )
