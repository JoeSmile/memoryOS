import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog

ACTION_DEMO_TURN = "demo_turn"
ACTION_LOGIN_FAILED = "login_failed"


def mask_email_for_audit(email: str) -> str:
    """Store domain only; avoid persisting full email in audit metadata."""
    _, _, domain = email.partition("@")
    if not domain:
        return "***"
    return f"***@{domain}"


class AuditRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def append(
        self,
        *,
        action: str,
        user_id: uuid.UUID | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditLog:
        row = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata_json=metadata or {},
        )
        self.db.add(row)
        await self.db.flush()
        await self.db.refresh(row)
        return row

    async def append_demo_turn(
        self,
        *,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
        template_id: str,
        match_id: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        return await self.append(
            action=ACTION_DEMO_TURN,
            user_id=user_id,
            resource_type="conversation",
            resource_id=str(conversation_id),
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={"template_id": template_id, "match_id": match_id},
        )

    async def append_login_failed(
        self,
        *,
        email: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        return await self.append(
            action=ACTION_LOGIN_FAILED,
            metadata={"email_masked": mask_email_for_audit(email)},
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def list_for_user_action(
        self,
        user_id: uuid.UUID,
        action: str,
    ) -> list[AuditLog]:
        result = await self.db.execute(
            select(AuditLog)
            .where(AuditLog.user_id == user_id, AuditLog.action == action)
            .order_by(AuditLog.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_by_action(self, action: str) -> list[AuditLog]:
        result = await self.db.execute(
            select(AuditLog)
            .where(AuditLog.action == action)
            .order_by(AuditLog.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_login_failed_for_email_masked(
        self,
        email_masked: str,
    ) -> list[AuditLog]:
        result = await self.db.execute(
            select(AuditLog)
            .where(
                AuditLog.action == ACTION_LOGIN_FAILED,
                AuditLog.metadata_json["email_masked"].as_string() == email_masked,
            )
            .order_by(AuditLog.created_at.desc())
        )
        return list(result.scalars().all())
