from fastapi import APIRouter

from app.schemas.error import ErrorCode, error_response_doc, success_response_doc

router = APIRouter(prefix="/health", tags=["health"])


@router.get(
    "",
    summary="Health check",
    description="Simple liveness endpoint used by orchestrators and monitoring.",
    responses={
        200: success_response_doc("Service is healthy", {"status": "ok"}),
        500: error_response_doc("Unexpected server error", ErrorCode.INTERNAL_ERROR, "An internal error occurred"),
    },
)
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
