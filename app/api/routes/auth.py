from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
async def register() -> dict[str, str]:
    return {"message": "register endpoint skeleton"}


@router.post("/login")
async def login() -> dict[str, str]:
    return {"message": "login endpoint skeleton"}


@router.post("/refresh")
async def refresh() -> dict[str, str]:
    return {"message": "refresh endpoint skeleton"}


@router.get("/me")
async def me() -> dict[str, str]:
    return {"message": "me endpoint skeleton"}
