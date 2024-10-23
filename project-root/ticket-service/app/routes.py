from fastapi import APIRouter, HTTPException
from .schemas import TicketCreate, TicketRead, TicketUpdate
from .models import Ticket
from .database import get_database
from bson import ObjectId

router = APIRouter()
db = get_database()
ticket_model = Ticket(db)

# ... (기존 코드 유지)

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
