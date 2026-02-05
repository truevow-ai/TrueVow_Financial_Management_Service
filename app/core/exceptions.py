"""Custom exceptions for FM Service"""
from fastapi import HTTPException, status


class FMServiceException(Exception):
    """Base exception for FM service"""
    pass


class ValidationError(FMServiceException):
    """Validation error"""
    pass


class NotFoundError(FMServiceException):
    """Resource not found"""
    pass


class UnauthorizedError(FMServiceException):
    """Unauthorized access"""
    pass


class BusinessRuleViolationError(FMServiceException):
    """Business rule violation"""
    pass


class PostingError(FMServiceException):
    """Journal entry posting error"""
    pass


class PeriodLockedError(FMServiceException):
    """Accounting period is locked"""
    pass


class DuplicateEntryError(FMServiceException):
    """Duplicate entry detected"""
    pass
