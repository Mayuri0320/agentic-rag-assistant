"""Health endpoint."""

from fastapi import APIRouter, Depends

from app.dependencies.services import get_health_service
from app.schemas.health import HealthResponse
from app.services.health_service import HealthService

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health(
    service: HealthService = Depends(get_health_service),
) -> HealthResponse:
    """Return application and dependency health."""
    dependencies = await service.check_dependencies()

    all_healthy = all(dependencies.values())

    return HealthResponse(
        status="healthy" if all_healthy else "degraded",
        database=dependencies["database"],
        redis=dependencies["redis"],
    )
