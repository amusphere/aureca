"""
Admin API endpoints for system management

Note: The old configuration management endpoints have been removed
as part of the system simplification. Configuration is now managed
through constants and environment variables.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/admin", tags=["admin"])

# Old configuration management endpoints have been removed
# Configuration is now handled through:
# - PlanLimits constants in app.constants.plan_limits
# - Environment variables for system settings
