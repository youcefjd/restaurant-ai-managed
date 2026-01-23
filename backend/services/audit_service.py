"""
Audit logging service for tracking admin actions.

Provides simple interface for logging admin actions for security and compliance.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class AuditService:
    """Service for logging admin actions."""

    def __init__(self, db):
        self.db = db

    def log_action(
        self,
        admin_email: str,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        old_value: Optional[Dict[str, Any]] = None,
        new_value: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[int]:
        """
        Log an admin action to the audit log.

        Args:
            admin_email: Email of the admin performing the action
            action: Type of action (create, update, delete, suspend, etc.)
            resource_type: Type of resource affected (restaurant, order, commission, etc.)
            resource_id: ID of the affected resource (optional)
            old_value: Previous state of the resource (for updates)
            new_value: New state of the resource (for updates/creates)
            metadata: Additional context (IP address, etc.)

        Returns:
            ID of the created audit log entry, or None if failed
        """
        try:
            result = self.db.table("audit_logs").insert({
                "admin_email": admin_email,
                "action": action,
                "resource_type": resource_type,
                "resource_id": str(resource_id) if resource_id else None,
                "old_value": old_value,
                "new_value": new_value,
                "metadata": metadata or {}
            }).execute()

            if result.data:
                return result.data[0].get("id")
            return None

        except Exception as e:
            # Log error but don't fail the main operation
            logger.error(f"Failed to create audit log: {str(e)}")
            return None

    def log_create(
        self,
        admin_email: str,
        resource_type: str,
        resource_id: str,
        new_value: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[int]:
        """Log a resource creation."""
        return self.log_action(
            admin_email=admin_email,
            action="create",
            resource_type=resource_type,
            resource_id=resource_id,
            new_value=new_value,
            metadata=metadata
        )

    def log_update(
        self,
        admin_email: str,
        resource_type: str,
        resource_id: str,
        old_value: Dict[str, Any],
        new_value: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[int]:
        """Log a resource update."""
        return self.log_action(
            admin_email=admin_email,
            action="update",
            resource_type=resource_type,
            resource_id=resource_id,
            old_value=old_value,
            new_value=new_value,
            metadata=metadata
        )

    def log_delete(
        self,
        admin_email: str,
        resource_type: str,
        resource_id: str,
        old_value: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[int]:
        """Log a resource deletion."""
        return self.log_action(
            admin_email=admin_email,
            action="delete",
            resource_type=resource_type,
            resource_id=resource_id,
            old_value=old_value,
            metadata=metadata
        )

    def log_suspend(
        self,
        admin_email: str,
        resource_type: str,
        resource_id: str,
        reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[int]:
        """Log a resource suspension (e.g., suspending a restaurant)."""
        return self.log_action(
            admin_email=admin_email,
            action="suspend",
            resource_type=resource_type,
            resource_id=resource_id,
            new_value={"suspended": True, "reason": reason},
            metadata=metadata
        )

    def log_activate(
        self,
        admin_email: str,
        resource_type: str,
        resource_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[int]:
        """Log a resource activation (e.g., reactivating a restaurant)."""
        return self.log_action(
            admin_email=admin_email,
            action="activate",
            resource_type=resource_type,
            resource_id=resource_id,
            new_value={"activated": True},
            metadata=metadata
        )

    def log_commission_update(
        self,
        admin_email: str,
        account_id: int,
        old_rate: float,
        new_rate: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[int]:
        """Log a commission rate change."""
        return self.log_action(
            admin_email=admin_email,
            action="commission_update",
            resource_type="restaurant",
            resource_id=str(account_id),
            old_value={"platform_commission_rate": old_rate},
            new_value={"platform_commission_rate": new_rate},
            metadata=metadata
        )


def get_audit_service(db) -> AuditService:
    """Factory function to create audit service instance."""
    return AuditService(db)
