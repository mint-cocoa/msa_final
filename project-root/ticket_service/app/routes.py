from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from .schemas import CreateTicketForm, TicketResponse
from .database import users_collection, parks_collection , ticket_collection
from .utils import create_ticket
from datetime import datetime
from . import models
import secrets
router = APIRouter(
    prefix="/tickets",
    tags=["Tickets"]
)

@router.post("/create_ticket", response_model=TicketResponse)
def create_ticket_endpoint(form: CreateTicketForm):
    # 사용자 정보를 가져옵니다.
    user = users_collection.find_one({"_id": ObjectId(form.user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    # 공원 컬렉션에서 park_ticket_id를 가진 티켓을 찾습니다.
    park = parks_collection.find_one({
        "tickets._id": ObjectId(form.park_ticket_id)
    })
    if not park:
        raise HTTPException(status_code=404, detail="공원 또는 티켓을 찾을 수 없습니다.")

    # 해당 티켓 정보를 가져옵니다.
    park_ticket = None
    for ticket in park.get('tickets', []):
        if ticket['_id'] == ObjectId(form.park_ticket_id):
            park_ticket = ticket
            break

    if not park_ticket:
        raise HTTPException(status_code=404, detail="티켓을 찾을 수 없습니다.")

    # 티켓 생성
    ticket_data = {
        "user_id": form.user_id,
        "park_id": str(park['_id']),
        "park_ticket_data": park_ticket,
        "purchase_date": datetime.utcnow().isoformat(),
        "amount": park_ticket['price'],
        "available_date": form.available_date,
        "token": secrets.token_urlsafe(32)
    }

    result = ticket_collection.insert_one(ticket_data)

    return result

@router.get("/get_ticket/{token}", response_model=TicketResponse)
def get_ticket_endpoint(token: str):
    ticket = ticket_collection.find_one({"token": token})
    if not ticket:
        raise HTTPException(status_code=404, detail="티켓을 찾을 수 없습니다.")
    return ticket

@router.post("/use_ticket/{token}")
def use_ticket_endpoint(token: str):
    ticket = ticket_collection.find_one({"token": token})
    if not ticket:
        raise HTTPException(status_code=404, detail="티켓을 찾을 수 없습니다.")
    else:
        ticket_collection.delete_one({"token": token})
        
        return {"message": "티켓이 사용되었습니다."}

