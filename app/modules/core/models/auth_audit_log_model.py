"""Auth Audit Log Model

TrueVow Security Contract v1 — Section 9: Auth Audit Logging

Every service must create an auth_audit_log table.

Required fields per contract:
  request_id         UUID
  event_type         VARCHAR   (auth_success | auth_failure | scope_rejected |
                                permission_denied | permission_service_unavailable)
  tenant_id          TEXT      — Clerk org_id (canonical cross-service tenant ID)
  clerk_user_id      VARCHAR   — Clerk sub claim
  endpoint           VARCHAR
  method             VARCHAR
  ip_address         VARCHAR
  user_agent         TEXT
  permission_checked VARCHAR   — the resource:action that was evaluated
  response_status    INTEGER
  details            JSONB
  created_at         TIMESTAMPTZ

Additional fields added by FM service:
  scope              VARCHAR   — "internal" | "tenant"
  correlation_id     VARCHAR   — X-Correlation-ID header
  fm_role            VARCHAR   — FM RBAC role at time of event
"""
import uuid
from sqlalchemy import Column, DateTime, Integer, String, Text, Index
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy import func
from app.core.db_metadata import Base


class AuthAuditLog(Base):
    """
    Immutable per-request authentication audit log.

    Written by app/auth/authorization.py on every auth event.
    Never updated or deleted — append-only.

    Event types (contract Section 9):
      auth_success                    — JWT verified, scope OK, permissions loaded
      auth_failure                    — JWT invalid, expired, or malformed
      scope_rejected                  — JWT scope not allowed for this service
      permission_denied               — User lacks required permission
      permission_service_unavailable  — DB permission query failed (fail-CLOSED)
    """
    __tablename__ = "auth_audit_log"

    # Identity
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Event UUID primary key.",
    )
    request_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        comment="UUID generated at middleware entry for this request.",
    )

    # Event classification
    event_type = Column(
        String(60),
        nullable=False,
        index=True,
        comment=(
            "auth_success | auth_failure | scope_rejected | "
            "permission_denied | permission_service_unavailable"
        ),
    )

    # Identity
    tenant_id = Column(
        Text,
        nullable=True,
        index=True,
        comment="Clerk org_id (TEXT) — canonical cross-service tenant identifier.",
    )
    clerk_user_id = Column(
        String(255),
        nullable=True,
        index=True,
        comment="Clerk sub claim (user_xxxx).",
    )
    scope = Column(
        String(30),
        nullable=True,
        comment="JWT scope: internal | tenant.",
    )
    fm_role = Column(
        String(60),
        nullable=True,
        comment="FM RBAC role at time of event.",
    )

    # Request context
    endpoint = Column(
        String(500),
        nullable=True,
        comment="Request path (e.g. /api/v1/books/{book_id}/journal-entries).",
    )
    method = Column(
        String(10),
        nullable=True,
        comment="HTTP method: GET | POST | PUT | PATCH | DELETE.",
    )
    ip_address = Column(
        String(45),
        nullable=True,
        comment="Client IP address (IPv4 or IPv6).",
    )
    user_agent = Column(
        Text,
        nullable=True,
        comment="User-Agent header value.",
    )
    correlation_id = Column(
        String(100),
        nullable=True,
        comment="X-Correlation-ID header value.",
    )

    # What was checked
    permission_checked = Column(
        String(200),
        nullable=True,
        comment="The resource:action permission that was evaluated (if any).",
    )
    response_status = Column(
        Integer,
        nullable=True,
        comment="HTTP response status code.",
    )

    # Extra context
    details = Column(
        JSONB,
        nullable=True,
        comment="Structured details: error message, matched role, etc.",
    )

    # Timestamp
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        comment="UTC timestamp when the auth event was recorded.",
    )

    __table_args__ = (
        Index("idx_aal_tenant_time",    "tenant_id",      "created_at"),
        Index("idx_aal_user_time",      "clerk_user_id",  "created_at"),
        Index("idx_aal_event_time",     "event_type",     "created_at"),
        Index("idx_aal_correlation",    "correlation_id"),
        {
            "comment": (
                "Auth audit log per Security Contract v1 Section 9. "
                "Append-only — never update or delete rows."
            )
        },
    )

    def __repr__(self) -> str:
        return (
            f"<AuthAuditLog("
            f"event={self.event_type}, "
            f"user={self.clerk_user_id}, "
            f"tenant={self.tenant_id}, "
            f"status={self.response_status}, "
            f"at={self.created_at}"
            f")>"
        )
