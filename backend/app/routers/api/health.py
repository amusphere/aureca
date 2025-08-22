"""
Health check and environment validation endpoints.

This module provides endpoints for checking application health
and validating environment configuration.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config.stripe import StripeConfig

router = APIRouter(prefix="/health", tags=["health"])


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    message: str
    version: str = "1.0.0"


class EnvironmentValidationResponse(BaseModel):
    """Environment validation response model."""

    status: str
    stripe_configured: bool
    stripe_environment: str
    stripe_warnings: list[str]
    database_connected: bool = True  # TODO: Add actual DB health check


@router.get("/", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Basic health check endpoint."""
    return HealthResponse(status="healthy", message="Application is running")


@router.get("/environment", response_model=EnvironmentValidationResponse)
async def validate_environment() -> EnvironmentValidationResponse:
    """Validate environment configuration."""
    try:
        # Validate Stripe configuration
        stripe_validation = StripeConfig.validate_configuration()

        return EnvironmentValidationResponse(
            status="ok" if stripe_validation["is_configured"] else "warning",
            stripe_configured=stripe_validation["is_configured"],
            stripe_environment=stripe_validation["environment"],
            stripe_warnings=stripe_validation["warnings"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Environment validation failed: {str(e)}") from e
