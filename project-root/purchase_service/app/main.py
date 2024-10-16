from fastapi import FastAPI
from .routes import router as purchase_router

app = FastAPI(
    title="Purchase Service",
    description="Service for purchasing tickets",
    version="1.0.0"
)

app.include_router(purchase_router, prefix="/api")