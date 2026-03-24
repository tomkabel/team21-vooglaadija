from pydantic import BaseModel, HttpUrl


class DownloadCreate(BaseModel):
    url: HttpUrl


class DownloadResponse(BaseModel):
    id: str
    status: str
    url: str
