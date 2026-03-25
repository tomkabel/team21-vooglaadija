from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, downloads, health
from app.config import settings

app = FastAPI(title="YouTube Link Processor")

# Configure CORS
origins = settings.cors_origins.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(downloads.router, prefix="/api/v1")
app.include_router(health.router, prefix="/api/v1")


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "YouTube Link Processor API"}
