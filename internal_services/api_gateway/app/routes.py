# routers/tickets.py
from fastapi import APIRouter, HTTPException, status
from database import redis_client
from models import UseTicketResponse
import httpx
import os

router = APIRouter()

TICKET_SERVICE_URL = os.getenv("TICKET_SERVICE_URL", "http://ticket-service:8000")

@router.post("/use_ticket/{token}", response_model=UseTicketResponse, responses={404: {"model": dict}})
async def use_ticket_endpoint(token: str):
    async with httpx.AsyncClient() as client:
        # 티켓 서비스에 티켓 유효성 확인 요청
        response = await client.get(f"{TICKET_SERVICE_URL}/api/tickets/validate/{token}")
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.json().get("detail", "티켓을 찾을 수 없거나 유효하지 않습니다."))
        
        ticket_data = response.json()
        
        # 티켓 사용 처리 요청
        use_response = await client.post(f"{TICKET_SERVICE_URL}/api/tickets/use/{token}")
        
        if use_response.status_code != 200:
            raise HTTPException(status_code=use_response.status_code, detail=use_response.json().get("detail", "티켓 사용 처리 중 오류가 발생했습니다."))
    
    # Redis에 게스트 정보 저장
    guest_id = str(ticket_data.get("id"))
    guest_info = {
        "token": token,
        "used_at": ticket_data.get("updated_at"),
        "user_id": ticket_data.get("user_id"),
        "park_id": ticket_data.get("park_id"),
        "facility_id": ticket_data.get("facility_id")
    }
    
    await redis_client.hset(f"guest:{guest_id}", mapping=guest_info)
    
    # 현재 게스트 수 계산
    guest_keys = await redis_client.keys("guest:*")
    guest_count = len(guest_keys)
    
    return UseTicketResponse(message="티켓이 사용되었습니다.", guest_count=guest_count)
