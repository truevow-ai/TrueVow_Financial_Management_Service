"""Approval Policy Repository"""
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.shared.repositories.base_repository import BaseRepository
from app.modules.core.models.approval_policy_model import ApprovalPolicy, ApprovalObjectType


class ApprovalPolicyRepository(BaseRepository[ApprovalPolicy]):
    """Repository for approval policies"""
    
    async def get_by_entity_and_type(
        self,
        entity_id: UUID,
        object_type: ApprovalObjectType
    ) -> Optional[ApprovalPolicy]:
        """Get approval policy for entity and object type"""
        stmt = select(ApprovalPolicy).where(
            ApprovalPolicy.legal_entity_id == entity_id,
            ApprovalPolicy.object_type == object_type
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def is_approval_required(
        self,
        entity_id: UUID,
        object_type: ApprovalObjectType
    ) -> bool:
        """Check if approval is required for entity and object type (defaults to True)"""
        policy = await self.get_by_entity_and_type(entity_id, object_type)
        if policy is None:
            return True  # Default: approval required
        return policy.approval_required
