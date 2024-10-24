from fastapi import FastAPI
from .routes import router as ticket_router

app = FastAPI(
    title="Ticket Service",
    description="Service for managing tickets",
    version="1.0.0",
    root_path="/tickets"
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Ticket Service"}

app.include_router(ticket_router, prefix="/api")