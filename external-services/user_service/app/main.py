# user_service/app/main.py
from fastapi import FastAPI
from .routes import router as user_router
from .database import Database

app = FastAPI(
    title="User Service",
    description="Service for managing users",
    version="1.0.0",
    root_path="/users"
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the User Service"}

@app.on_event("startup")
async def startup_db_client():
    await Database.connect_db()

@app.on_event("shutdown")
async def shutdown_db_client():
    await Database.close_db()
  
app.include_router(user_router, prefix="/api")  # '/api' 대신 '/users'를 사용
