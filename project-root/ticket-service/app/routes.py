from fastapi import APIRouter, HTTPException
from .schemas import TicketCreate, TicketRead, TicketUpdate
from .models import Ticket
from .database import get_database
from bson import ObjectId

router = APIRouter()
db = get_database()
ticket_model = Ticket(db)

@router.post("/tickets", response_model=TicketRead)
async def create_ticket(ticket: TicketCreate):
    ticket_id = await ticket_model.create_ticket(ticket.dict())
    created_ticket = await ticket_model.get_ticket(ticket_id)
    return {
        "id": ticket_id,
        "user_id": str(created_ticket["user_id"]),
        "park_id": str(created_ticket["park_id"]),
        "facility_id": str(created_ticket["facility_id"]),
        "status": created_ticket["status"],
        "created_at": created_ticket["created_at"],
        "updated_at": created_ticket["updated_at"],
    }

@router.get("/tickets/{ticket_id}", response_model=TicketRead)
async def get_ticket(ticket_id: str):
    ticket = await ticket_model.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return {
        "id": str(ticket["_id"]),
        "user_id": str(ticket["user_id"]),
        "park_id": str(ticket["park_id"]),
        "facility_id": str(ticket["facility_id"]),
        "status": ticket["status"],
        "created_at": ticket["created_at"],
        "updated_at": ticket["updated_at"],
    }

@router.put("/tickets/{ticket_id}", response_model=TicketRead)
async def update_ticket(ticket_id: str, ticket: TicketUpdate):
    update_data = ticket.dict(exclude_unset=True)
    modified_count = await ticket_model.update_ticket(ticket_id, update_data)
    if modified_count == 0:
        raise HTTPException(status_code=404, detail="Ticket not found or no changes made")
    updated_ticket = await ticket_model.get_ticket(ticket_id)
    return {
        "id": ticket_id,
        "user_id": str(updated_ticket["user_id"]),
        "park_id": str(updated_ticket["park_id"]),
        "facility_id": str(updated_ticket["facility_id"]),
        "status": updated_ticket["status"],
        "created_at": updated_ticket["created_at"],
        "updated_at": updated_ticket["updated_at"],
    }

@router.delete("/tickets/{ticket_id}")
async def delete_ticket(ticket_id: str):
    deleted_count = await ticket_model.delete_ticket(ticket_id)
    if deleted_count == 0:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return {"message": "Ticket deleted successfully"}

@router.get("/tickets/validate/{token}", response_model=TicketRead)
async def validate_ticket(token: str):
    ticket = await ticket_model.get_ticket_by_token(token)
    if not ticket:
        raise HTTPException(status_code=404, detail="티켓을 찾을 수 없습니다.")
    if ticket["status"] != "active":
        raise HTTPException(status_code=400, detail="유효하지 않은 티켓입니다.")
    return {
        "id": str(ticket["_id"]),
        "user_id": str(ticket["user_id"]),
        "park_id": str(ticket["park_id"]),
        "facility_id": str(ticket["facility_id"]),
        "status": ticket["status"],
        "created_at": ticket["created_at"],
        "updated_at": ticket["updated_at"],
    }

@router.post("/tickets/use/{token}", response_model=TicketRead)
async def use_ticket(token: str):
    ticket = await ticket_model.get_ticket_by_token(token)
    if not ticket:
        raise HTTPException(status_code=404, detail="티켓을 찾을 수 없습니다.")
    if ticket["status"] != "active":
        raise HTTPException(status_code=400, detail="이미 사용된 티켓입니다.")
    
    updated_ticket = await ticket_model.update_ticket_status(str(ticket["_id"]), "used")
    return {
        "id": str(updated_ticket["_id"]),
        "user_id": str(updated_ticket["user_id"]),
        "park_id": str(updated_ticket["park_id"]),
        "facility_id": str(updated_ticket["facility_id"]),
        "status": updated_ticket["status"],
        "created_at": updated_ticket["created_at"],
        "updated_at": updated_ticket["updated_at"],
    }
