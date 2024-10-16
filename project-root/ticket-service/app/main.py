from fastapi import FastAPI
from .routes import router as ticket_router

app = FastAPI(
    title="Ticket Service",
    description="Service for managing tickets",
    version="1.0.0"
)

app.include_router(ticket_router, prefix="/api")