# structure_manager/main.py
from fastapi import FastAPI
from .routes import router
from .database import Database

app = FastAPI(
    title="Structure Manager",
    description="Service for managing park structure and access control",
    version="1.0.0",
    root_path="/structure"
)

@app.on_event("startup")
async def startup_db_client():
    await Database.connect_db()

@app.on_event("shutdown")
async def shutdown_db_client():
    await Database.close_db()

app.include_router(router, prefix="/api")
