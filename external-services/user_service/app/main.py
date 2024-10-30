# user_service/app/main.py
from fastapi import FastAPI
from .routes import router as user_router
from .database import Database
from common.rabbitmq import RabbitMQConnection
import logging

app = FastAPI(
    title="User Service",
    description="Service for managing users",
    version="1.0.0",
    root_path="/users"
)

@app.on_event("startup")
async def startup_event():
    await Database.connect_db()
    await RabbitMQConnection.connect()
    logging.info("User Service started")

@app.on_event("shutdown")
async def shutdown_event():
    await Database.close_db()
    await RabbitMQConnection.close()
    logging.info("User Service shutdown")

@app.get("/")
def read_root():
    return {"message": "Welcome to the User Service"}

app.include_router(user_router, prefix="/api")
