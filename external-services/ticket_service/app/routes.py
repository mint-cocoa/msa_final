from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId

from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from .config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from .utils import create_access_token 
from .models import CreateTicketForm, TicketResponse
from motor.motor_asyncio import AsyncIOMotorClient
from .database import get_database

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")



router = APIRouter()
@router.post("/")
async def create_ticket_endpoint(form: CreateTicketForm, db = Depends(get_database)):
    # 컬렉션 참조
    users_collection = db.users
    parks_collection = db.parks
    tickets_collection = db.tickets

    # 사용자 검색
    user = await users_collection.findById(form.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user not found.")

    # 공원 검색
    park = await parks_collection.findById(form.park_id)
    if not park:
        raise HTTPException(status_code=404, detail="park not found.")

    # 공원의 티켓 타입 목록에서 해당 이름의 티켓을 찾습니다
    park_ticket = next((ticket for ticket in park.get('ticket_types', []) 
                       if ticket['name'] == form.ticket_type_name), None)
    if not park_ticket:
        raise HTTPException(status_code=404, detail="ticket not found.")

    # 티켓 생성
    ticket_data = {
        "user_id": form.user_id,
        "park_id": str(park['_id']),
        "ticket_type_name": park_ticket['name'],
        "allowed_facilities": park_ticket['allowed_facilities'],
        "purchase_date": datetime.utcnow().isoformat(),
        "amount": park_ticket['price'],
        "available_date": form.available_date,
        "used": False
    }

    result = await tickets_collection.insert_one(ticket_data)

    return {
        "ticket_id": str(result.inserted_id),
        "message": "ticket created successfully."
    }

@router.post("/use/{ticket_id}")
async def use_ticket(ticket_id: str, db = Depends(get_database)):
    tickets_collection = db.tickets
    ticket = await tickets_collection.findById(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="ticket not found.")
    if ticket["used"]:
        raise HTTPException(status_code=400, detail="ticket already used.")
    
    # 티켓 사용 처리
    await tickets_collection.updateOne(
        {"_id": ObjectId(ticket_id)}, 
        {"$set": {"used": True, "used_at": datetime.utcnow().isoformat()}}
    )
    
    # JWT 토큰 생성
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": str(ticket["_id"]),
            "user_id": ticket["user_id"],
            "park_id": ticket["park_id"],
            "ticket_type_name": ticket["ticket_type_name"],
            "allowed_facilities": ticket["allowed_facilities"]
        },
        expires_delta=access_token_expires
    )
    
    return {
        "message": "ticket used successfully.", 
        "access_token": access_token, 
        "token_type": "bearer"
    }

@router.get("/verify_ticket")
async def verify_ticket(token: str = Depends(oauth2_scheme), db: AsyncIOMotorClient = Depends(get_database)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        ticket_id = payload.get("sub")
        if ticket_id is None:
            raise HTTPException(status_code=401, detail="invalid ticket.")
        
        ticket = await db["tickets"].find_one({"_id": ObjectId(ticket_id)})
        if not ticket or not ticket["used"]:
            raise HTTPException(status_code=401, detail="invalid ticket.")
        
        return {
            "message": "valid ticket.",
            "ticket_data": {
                "user_id": payload.get("user_id"),
                "park_id": payload.get("park_id"),
                "ticket_type_name": payload.get("ticket_type_name"),
                "allowed_facilities": payload.get("allowed_facilities")
            }
        }
    except JWTError:
        raise HTTPException(status_code=401, detail="invalid token.")
