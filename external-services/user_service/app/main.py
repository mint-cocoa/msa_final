# user_service/app/main.py
from fastapi import FastAPI
from .routes import router as user_router


app = FastAPI(
    title="User Service",
    description="Service for managing users",
    version="1.0.0",
    root_path="/users"
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the User Service"}

app.include_router(user_router, prefix="/users")  # '/api' 대신 '/users'를 사용
