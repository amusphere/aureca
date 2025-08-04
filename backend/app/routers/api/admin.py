"""
Admin API endpoints for configuration management
"""


from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session

from app.config import config_manager, get_all_ai_chat_plans, update_ai_chat_plan_limit
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
        )


@router.get("/ai-chat/plans/{plan_name}", response_model=PlanConfigResponse)
async def get_ai_chat_plan_endpoint(
    plan_name: str, session: Session = Depends(get_session)
) -> PlanConfigResponse:
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
        )


@router.put("/ai-chat/plans/{plan_name}")
async def update_ai_chat_plan_endpoint(
    plan_name: str,
    request: PlanLimitUpdateRequest,
    session: Session = Depends(get_session),
) -> dict[str, str]:
    """
    Update AI chat plan configuration

    Args:
        plan_name: Name of the plan to update
        request: Plan update request data

    Returns:
        Dict with success message
    """
    try:
        # Validate daily limit
        if request.daily_limit < -1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Daily limit must be -1 (unlimited) or a non-negative integer",
            )

        # Update the plan configuration
        success = update_ai_chat_plan_limit(
            plan_name=request.plan_name or plan_name,
            daily_limit=request.daily_limit,
            description=request.description,
            features=request.features,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update plan configuration for '{plan_name}'",
            )

        return {
            "message": f"Successfully updated plan '{plan_name}' with daily limit: {request.daily_limit}",
            "plan_name": plan_name,
            "daily_limit": str(request.daily_limit),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update plan configuration: {str(e)}",
        )


@router.post("/ai-chat/plans")
async def create_ai_chat_plan_endpoint(
    request: PlanLimitUpdateRequest, session: Session = Depends(get_session)
) -> dict[str, str]:
    """
    Create new AI chat plan configuration

    Args:
        request: Plan creation request data

    Returns:
        Dict with success message
    """
    try:
        # Validate daily limit
        if request.daily_limit < -1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Daily limit must be -1 (unlimited) or a non-negative integer",
            )

        # Check if plan already exists
        existing_plans = get_all_ai_chat_plans()
        if request.plan_name in existing_plans:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Plan '{request.plan_name}' already exists. Use PUT to update.",
            )

        # Create the new plan configuration
        success = update_ai_chat_plan_limit(
            plan_name=request.plan_name,
            daily_limit=request.daily_limit,
            description=request.description or f"{request.plan_name} plan",
            features=request.features or [],
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create plan configuration for '{request.plan_name}'",
            )

        return {
            "message": f"Successfully created plan '{request.plan_name}' with daily limit: {request.daily_limit}",
            "plan_name": request.plan_name,
            "daily_limit": str(request.daily_limit),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create plan configuration: {str(e)}",
        )


@router.get("/ai-chat/config/reload")
async def reload_ai_chat_config_endpoint() -> dict[str, str]:
    """
    Reload AI chat configuration from file

    Returns:
        Dict with success message
    """
    try:
        # Force reload by checking file updates
        config_manager._check_file_updates()

        return {
            "message": "Configuration reloaded successfully",
            "timestamp": (
                str(config_manager._last_modified)
                if config_manager._last_modified
                else "No file configured"
            ),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reload configuration: {str(e)}",
        )
