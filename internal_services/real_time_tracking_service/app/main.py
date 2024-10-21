from fastapi import FastAPI
from .kafka_consumer import start_kafka_consumer
import asyncio

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(start_kafka_consumer())

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
