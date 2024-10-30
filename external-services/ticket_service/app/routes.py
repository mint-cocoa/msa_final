from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from .config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from .utils import create_access_token 
from .models import CreateTicketForm
from motor.motor_asyncio import AsyncIOMotorClient
from .database import get_db
from .external_api import get_user_info, get_park_info
from fastapi import Request
import httpx

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")



router = APIRouter()
@router.post("/")
async def create_ticket_endpoint(form: CreateTicketForm, db = Depends(get_db)):

    user = await get_user_info(form.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user not found.")          

    # 공원 검색
    park = await get_park_info(form.park_id)
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
        "used": False
    }

    result = await db["tickets"].insert_one(ticket_data)

    return {
        "ticket_id": str(result.inserted_id),
        "message": "ticket created successfully."
    }

@router.post("/use/{ticket_id}")
async def use_ticket(ticket_id: str, db: AsyncIOMotorClient = Depends(get_db)):
    ticket = await db["tickets"].find_one({"_id": ObjectId(ticket_id)})
    if not ticket:
        raise HTTPException(status_code=404, detail="ticket not found.")
    if ticket["used"]:
        raise HTTPException(status_code=400, detail="ticket already used.")
    
    # 티켓 사용 처리
    await db["tickets"].update_one(
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
async def verify_ticket(token: str = Depends(oauth2_scheme), db: AsyncIOMotorClient = Depends(get_db)):
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

@router.post("/validate/{ticket_id}")
async def validate_ticket(
    ticket_id: str,
    facility_id: str,
    request: Request
):
    db = await get_db()
    ticket = await db.tickets.find_one({"_id": ObjectId(ticket_id)})
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
        
    # Structure Manager에서 접근 권한 확인
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{STRUCTURE_MANAGER_URL}/api/access-control/{ticket['ticket_type_id']}"
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=403, detail="Access control not found")
            
        access_control = response.json()
        if ObjectId(facility_id) not in [ObjectId(fid) for fid in access_control['facility_ids']]:
            raise HTTPException(status_code=403, detail="Access denied to this facility")
    
    return {"valid": True, "ticket": ticket}

@router.put("/ticket-types/{ticket_type_id}")
async def update_ticket_type(ticket_type_id: str, ticket_type: TicketTypeUpdate, request: Request):
    # Structure Manager에 검증 요청
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{STRUCTURE_MANAGER_URL}/api/validate/ticket-type-update/{ticket_type_id}"
        )
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to validate update")
        
        validation = response.json()
        if not validation["can_update"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot update ticket type. Has {validation['active_tickets_count']} active tickets."
            )
    
    db = await get_db()
    result = await db.ticket_types.update_one(
        {"_id": ObjectId(ticket_type_id)},
        {"$set": ticket_type.dict(exclude_unset=True)}
    )
