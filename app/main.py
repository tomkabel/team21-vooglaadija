from fastapi import FastAPI

from app.api.routes import auth, downloads, health

app = FastAPI(title="YouTube Link Processor")

app.include_router(auth.router, prefix="/api/v1")
app.include_router(downloads.router, prefix="/api/v1")
app.include_router(health.router, prefix="/api/v1")


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "YouTube Link Processor API"}
