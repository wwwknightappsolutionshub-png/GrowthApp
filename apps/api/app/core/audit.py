import logging
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.models import AuditLog

logger = logging.getLogger(__name__)


async def log_action(
    db: AsyncSession,
    action: str,
    resource: str,
    resource_id: str | UUID | None = None,
    user_id: UUID | None = None,
    tenant_id: UUID | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Write an audit log entry. Never raises — logs a warning on failure.

    The entry is added to the current session and flushed; the caller's outer
    transaction is responsible for committing. If the flush fails we swallow
    the error so audit-logging never blocks the user-visible action.
    """
    try:
        entry = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            resource=resource,
            resource_id=str(resource_id) if resource_id else None,
            ip_address=ip_address,
            user_agent=user_agent,
            extra_metadata=metadata or {},
        )
        db.add(entry)
        await db.flush()
    except Exception as exc:
        logger.warning("Failed to write audit log [%s/%s]: %s", resource, action, exc)
