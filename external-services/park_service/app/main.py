# park_service/app/main.py
from fastapi import FastAPI
from .routes import router as park_router

app = FastAPI(
    title="Park Service",
    description="Service for managing parks",
    version="1.0.0",
    root_path="/parks"
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Park Service"}

app.include_router(park_router, prefix="/api")