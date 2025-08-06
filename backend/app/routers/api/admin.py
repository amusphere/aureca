"""
Admin API endpoints for configuration management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session

from app.config.manager import config_manager
from app.database import get_session
from app.services.ai_chat_usage_service import AIChatUsageService

router = APIRouter(prefix="/admin", tags=["admin"])


class PlanLimitUpdateRequest(BaseModel):
    """Request model for updating plan limits"""

    plan_name: str
    daily_limit: int
    description: str = None
    features: list[str] = None


class PlanConfigResponse(BaseModel):
    """Response model for plan configuration"""

    plan_name: str
    daily_limit: int
    description: str
    features: list[str]


class AllPlansResponse(BaseModel):
    """Response model for all plan configurations"""

    plans: dict[str, PlanConfigResponse]
    total_plans: int


@router.get("/ai-chat/plans", response_model=AllPlansResponse)
async def get_all_ai_chat_plans_endpoint(
    session: Session = Depends(get_session),
) -> AllPlansResponse:
    """
    Get all AI chat plan configurations

    Returns:
        AllPlansResponse: All plan configurations
    """
    try:
        usage_service = AIChatUsageService(session)
        all_configs = usage_service.get_all_plan_configs()

        plans = {}
        for plan_name, config in all_configs.items():
            plans[plan_name] = PlanConfigResponse(
                plan_name=plan_name,
                daily_limit=config["daily_limit"],
                description=config["description"],
                features=config["features"],
            )

        return AllPlansResponse(plans=plans, total_plans=len(plans))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve plan configurations: {str(e)}",
        ) from e


@router.get("/ai-chat/plans/{plan_name}", response_model=PlanConfigResponse)
async def get_ai_chat_plan_endpoint(plan_name: str, session: Session = Depends(get_session)) -> PlanConfigResponse:
    """
    Get specific AI chat plan configuration

    Args:
        plan_name: Name of the plan to retrieve

    Returns:
        PlanConfigResponse: Plan configuration
    """
    try:
        usage_service = AIChatUsageService(session)
        config = usage_service.get_plan_config(plan_name)

        return PlanConfigResponse(
            plan_name=config["plan_name"],
            daily_limit=config["daily_limit"],
            description=config["description"],
            features=config["features"],
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve plan configuration for '{plan_name}': {str(e)}",
        ) from e


@router.put("/ai-chat/plans/{plan_name}")
async def update_ai_chat_plan_endpoint(
    plan_name: str,
    request: PlanLimitUpdateRequest,
    session: Session = Depends(get_session),
) -> dict[str, str]:
    """
    Update AI chat plan configuration

    NOTE: This endpoint is deprecated. Configuration file updates are disabled
    to prevent file pollution. Use database-based configuration instead.

    Args:
        plan_name: Name of the plan to update
        request: Plan update request data

    Returns:
        Dict with warning message
    """
    # Validate daily limit even though we won't update
    if request.daily_limit < -1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Daily limit must be -1 (unlimited) or a non-negative integer",
        )

    # Return warning instead of attempting to update
    return {
        "message": f"Configuration updates are disabled. Plan '{plan_name}' update ignored.",
        "plan_name": plan_name,
        "warning": "Use database-based configuration for dynamic plan management",
    }


@router.post("/ai-chat/plans")
async def create_ai_chat_plan_endpoint(
    request: PlanLimitUpdateRequest, session: Session = Depends(get_session)
) -> dict[str, str]:
    """
    Create new AI chat plan configuration

    NOTE: This endpoint is deprecated. Configuration file updates are disabled
    to prevent file pollution. Use database-based configuration instead.

    Args:
        request: Plan creation request data

    Returns:
        Dict with warning message
    """
    # Validate daily limit even though we won't create
    if request.daily_limit < -1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Daily limit must be -1 (unlimited) or a non-negative integer",
        )

    # Return warning instead of attempting to create
    return {
        "message": f"Configuration creation is disabled. Plan '{request.plan_name}' creation ignored.",
        "plan_name": request.plan_name,
        "warning": "Use database-based configuration for dynamic plan management",
    }


@router.get("/ai-chat/config/reload")
async def reload_ai_chat_config_endpoint() -> dict[str, str]:
    """
    Reload AI chat configuration from file

    Returns:
        Dict with success message
    """
    try:
        # Force reload by clearing cached data
        config_manager._config_data = None
        config_manager._ai_chat_plans = None

        # Test that the config can be loaded successfully
        config_manager._load_config()

        return {
            "message": "Configuration cache cleared and reloaded successfully",
            "timestamp": "Cache cleared",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reload configuration: {str(e)}",
        ) from e
