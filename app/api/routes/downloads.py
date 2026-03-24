from fastapi import APIRouter

router = APIRouter(prefix="/downloads", tags=["downloads"])


@router.post("")
async def create_download() -> dict[str, str]:
    return {"message": "create download skeleton"}


@router.get("")
async def list_downloads() -> dict[str, str]:
    return {"message": "list downloads skeleton"}


@router.get("/{job_id}")
async def get_download(job_id: str) -> dict[str, str]:
    return {"message": f"download {job_id} status skeleton"}


@router.get("/{job_id}/file")
async def get_download_file(job_id: str) -> dict[str, str]:
    return {"message": f"download file {job_id} skeleton"}


@router.delete("/{job_id}")
async def delete_download(job_id: str) -> dict[str, str]:
    return {"message": f"delete download {job_id} skeleton"}
