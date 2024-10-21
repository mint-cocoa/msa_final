from fastapi import APIRouter, HTTPException, Depends
from .database import get_db
from . import models
from jose import jwt
from datetime import datetime, timedelta
from typing import Optional

router = APIRouter()

SECRET_KEY = "your-secret-key"  # 실제 운영 환경에서는 환경 변수로 관리해야 합니다.
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24시간

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@router.get("/validate/{token}")
async def validate_ticket(token: str, db=Depends(get_db)):
    ticket = await db.tickets.find_one({"token": token})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return {"valid": True, "ticket_info": ticket}

@router.post("/use/{token}")
async def use_ticket(token: str, db=Depends(get_db)):
    ticket = await db.tickets.find_one({"token": token})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if ticket["used"]:
        raise HTTPException(status_code=400, detail="Ticket already used")
    
    # 티켓 사용 처리
    await db.tickets.update_one({"token": token}, {"$set": {"used": True, "used_at": datetime.utcnow()}})
    
    # JWT 토큰 생성
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(ticket["_id"]), "user_id": ticket["user_id"], "park_id": ticket["park_id"]},
        expires_delta=access_token_expires
    )
    
    return {"message": "Ticket used successfully", "access_token": access_token, "token_type": "bearer"}
