"""Role-Based Access Control (RBAC) System.
Implements the 5 primary actors defined in business requirements:
1. Customer/Prospect: Represented through contact records and journey events.
2. Marketing/Sales Operations: Manage campaigns, budgets, channels and customer journeys.
3. Support Agent: View customer profiles and chronological interactions (read-only).
4. Analyst: Access attribution analysis, ROI analytics, anomaly evaluation and reports.
5. System Administrator: Manage dataset generation, validation, exports, application settings.
"""
from enum import Enum
from typing import List, Dict, Any, Optional
from fastapi import Header, HTTPException, status, Depends

class RoleEnum(str, Enum):
    CUSTOMER_PROSPECT = "CUSTOMER_PROSPECT"
    MARKETING_SALES_OPS = "MARKETING_SALES_OPS"
    SUPPORT_AGENT = "SUPPORT_AGENT"
    ANALYST = "ANALYST"
    SYSTEM_ADMIN = "SYSTEM_ADMIN"

class PermissionEnum(str, Enum):
    VIEW_OWN_JOURNEY = "VIEW_OWN_JOURNEY"
    VIEW_ALL_JOURNEYS = "VIEW_ALL_JOURNEYS"
    VIEW_CAMPAIGNS = "VIEW_CAMPAIGNS"
    MANAGE_CAMPAIGNS = "MANAGE_CAMPAIGNS"
    VIEW_FINANCIALS = "VIEW_FINANCIALS"
    RUN_ATTRIBUTION = "RUN_ATTRIBUTION"
    VIEW_ANOMALIES = "VIEW_ANOMALIES"
    MANAGE_DATASET = "MANAGE_DATASET"
    EXPORT_DATA = "EXPORT_DATA"
    MANAGE_SETTINGS = "MANAGE_SETTINGS"

ROLE_PERMISSIONS: Dict[RoleEnum, List[PermissionEnum]] = {
    RoleEnum.CUSTOMER_PROSPECT: [
        PermissionEnum.VIEW_OWN_JOURNEY,
    ],
    RoleEnum.MARKETING_SALES_OPS: [
        PermissionEnum.VIEW_ALL_JOURNEYS,
        PermissionEnum.VIEW_CAMPAIGNS,
        PermissionEnum.MANAGE_CAMPAIGNS,
        PermissionEnum.VIEW_FINANCIALS,
    ],
    RoleEnum.SUPPORT_AGENT: [
        PermissionEnum.VIEW_ALL_JOURNEYS,
        PermissionEnum.VIEW_CAMPAIGNS,
    ],
    RoleEnum.ANALYST: [
        PermissionEnum.VIEW_ALL_JOURNEYS,
        PermissionEnum.VIEW_CAMPAIGNS,
        PermissionEnum.VIEW_FINANCIALS,
        PermissionEnum.RUN_ATTRIBUTION,
        PermissionEnum.VIEW_ANOMALIES,
        PermissionEnum.EXPORT_DATA,
    ],
    RoleEnum.SYSTEM_ADMIN: [
        PermissionEnum.VIEW_OWN_JOURNEY,
        PermissionEnum.VIEW_ALL_JOURNEYS,
        PermissionEnum.VIEW_CAMPAIGNS,
        PermissionEnum.MANAGE_CAMPAIGNS,
        PermissionEnum.VIEW_FINANCIALS,
        PermissionEnum.RUN_ATTRIBUTION,
        PermissionEnum.VIEW_ANOMALIES,
        PermissionEnum.MANAGE_DATASET,
        PermissionEnum.EXPORT_DATA,
        PermissionEnum.MANAGE_SETTINGS,
    ],
}

ROLE_ALLOWED_PAGES: Dict[RoleEnum, List[str]] = {
    RoleEnum.CUSTOMER_PROSPECT: ["journey"],
    RoleEnum.MARKETING_SALES_OPS: ["overview", "campaigns", "journey", "roi"],
    RoleEnum.SUPPORT_AGENT: ["journey", "campaigns"],
    RoleEnum.ANALYST: ["overview", "campaigns", "attribution", "roi", "anomalies", "reports"],
    RoleEnum.SYSTEM_ADMIN: ["overview", "campaigns", "journey", "attribution", "roi", "anomalies", "generator", "reports"],
}

ACTOR_PERSONAS: Dict[RoleEnum, Dict[str, Any]] = {
    RoleEnum.CUSTOMER_PROSPECT: {
        "user_id": "USR-CUST-001",
        "name": "Shravika Kavati",
        "email": "shravika.kavati@gmail.com",
        "role": RoleEnum.CUSTOMER_PROSPECT.value,
        "role_name": "Customer / Prospect",
        "title": "Customer / Prospect",
        "contact_id": "CON-2026-000001",
        "avatar_badge": "Customer",
        "description": "Represented through contact records and customer journey events. Access restricted to own interaction timeline."
    },
    RoleEnum.MARKETING_SALES_OPS: {
        "user_id": "USR-OPS-002",
        "name": "Sharanya Kavati",
        "email": "sharanya.kavati@marketing.enterprise.in",
        "role": RoleEnum.MARKETING_SALES_OPS.value,
        "role_name": "Marketing & Sales Operations",
        "title": "Campaign Operations Lead",
        "contact_id": None,
        "avatar_badge": "Marketing Ops",
        "description": "Manages campaigns, budgets, channels and customer journeys."
    },
    RoleEnum.SUPPORT_AGENT: {
        "user_id": "USR-SUP-003",
        "name": "Srinivas Kavati",
        "email": "srinivas.kavati@support.enterprise.in",
        "role": RoleEnum.SUPPORT_AGENT.value,
        "role_name": "Support Agent",
        "title": "Customer Support Specialist",
        "contact_id": None,
        "avatar_badge": "Support (Read-Only)",
        "description": "Views customer profiles and chronological interactions with appropriate read-only permissions."
    },
    RoleEnum.ANALYST: {
        "user_id": "USR-ANA-004",
        "name": "Shailaja Kavati",
        "email": "shailaja.kavati@analytics.enterprise.in",
        "role": RoleEnum.ANALYST.value,
        "role_name": "Attribution & Financial Analyst",
        "title": "Senior Attribution Analyst",
        "contact_id": None,
        "avatar_badge": "Analyst",
        "description": "Accesses attribution analysis, ROI analytics, anomaly evaluation and reports."
    },
    RoleEnum.SYSTEM_ADMIN: {
        "user_id": "USR-ADM-005",
        "name": "Krish Kavati",
        "email": "krish.kavati@admin.enterprise.in",
        "role": RoleEnum.SYSTEM_ADMIN.value,
        "role_name": "System Administrator",
        "title": "Platform Administrator",
        "contact_id": None,
        "avatar_badge": "Administrator",
        "description": "Manages dataset generation, validation, exports, application settings and user permissions."
    }
}

def get_current_user(
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id")
) -> Dict[str, Any]:
    """Resolves active user and role from request header. Defaults to SYSTEM_ADMIN if absent."""
    if x_user_role:
        try:
            role = RoleEnum(x_user_role.upper())
        except ValueError:
            role = RoleEnum.SYSTEM_ADMIN
    else:
        role = RoleEnum.SYSTEM_ADMIN

    persona = ACTOR_PERSONAS.get(role, ACTOR_PERSONAS[RoleEnum.SYSTEM_ADMIN]).copy()
    persona["permissions"] = [p.value for p in ROLE_PERMISSIONS[role]]
    persona["allowed_pages"] = ROLE_ALLOWED_PAGES[role]
    return persona

def require_roles(*allowed_roles: RoleEnum):
    """FastAPI dependency to enforce that current user possesses one of allowed roles."""
    def role_checker(user: Dict[str, Any] = Depends(get_current_user)):
        user_role_str = user["role"]
        try:
            user_role = RoleEnum(user_role_str)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Invalid user role: {user_role_str}"
            )

        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "ACCESS_DENIED",
                    "message": f"Role '{user_role.value}' does not have permission to access this resource.",
                    "user_role": user_role.value,
                    "allowed_roles": [r.value for r in allowed_roles]
                }
            )
        return user
    return role_checker
