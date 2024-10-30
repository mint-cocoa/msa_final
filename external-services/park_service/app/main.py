# park_service/app/main.py
from fastapi import FastAPI
from .routes import router as park_router
from common.rabbitmq import RabbitMQConnection
import logging

app = FastAPI(
    title="Park Service",
    description="Service for managing parks",
    version="1.0.0",
    root_path="/parks"
)

@app.on_event("startup")
async def startup_event():
    await RabbitMQConnection.connect()
    logging.info("Park Service started")

@app.on_event("shutdown")
async def shutdown_event():
    await RabbitMQConnection.close()
    logging.info("Park Service shutdown")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Park Service"}

app.include_router(park_router, prefix="/api")