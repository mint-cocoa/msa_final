# facility_service/app/main.py
from fastapi import FastAPI
from .routes import router as facility_router

app = FastAPI(
    title="Facility Service",
    description="Service for managing facilities",
    version="1.0.0",
    root_path="/facilities"
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Facility Service"}

app.include_router(facility_router, prefix="/api")