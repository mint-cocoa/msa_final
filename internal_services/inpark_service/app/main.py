from fastapi import FastAPI
from .routes import router as inpark_router

app = FastAPI(
    title="In-Park Service",
    description="Service for managing in-park guests and their activities",
    version="1.0.0"
)

app.include_router(inpark_router)
