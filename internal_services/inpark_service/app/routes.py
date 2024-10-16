from fastapi import APIRouter, HTTPException, Depends
from .models import UseTicketResponse, GuestInfo, RideReservation
from .dependencies import get_current_user
from .kafka_producer import send_queue_request
import httpx
import os
from typing import List
import asyncio

router = APIRouter()

TICKET_SERVICE_URL = os.getenv("TICKET_SERVICE_URL", "http://ticket-service:8000")
MESSAGE_BROKER_SERVICE_URL = os.getenv("MESSAGE_BROKER_SERVICE_URL", "http://message_broker_service:8000")
REDIS_SERVICE_URL = os.getenv("REDIS_SERVICE_URL", "http://redis-service:8000")

@router.post("/enter-park/{token}", response_model=UseTicketResponse)
async def enter_park(token: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{TICKET_SERVICE_URL}/api/tickets/validate/{token}")
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="티켓을 찾을 수 없거나 유효하지 않습니다.")
        
        ticket_data = response.json()
        
        use_response = await client.post(f"{TICKET_SERVICE_URL}/api/tickets/use/{token}")
        
        if use_response.status_code != 200:
            raise HTTPException(status_code=use_response.status_code, detail="티켓 사용 처리 중 오류가 발생했습니다.")
    
    guest_id = str(ticket_data.get("id"))
    guest_info = {
        "id": guest_id,
        "token": token,
        "entered_at": ticket_data.get("updated_at"),
        "user_id": ticket_data.get("user_id"),
        "park_id": ticket_data.get("park_id")
    }
    
    async with httpx.AsyncClient() as client:
        await client.post(f"{REDIS_SERVICE_URL}/guest", json=guest_info)
        guest_count_response = await client.get(f"{REDIS_SERVICE_URL}/guest_count")
        guest_count = guest_count_response.json()["guest_count"]
    
    return UseTicketResponse(message="공원에 입장하였습니다.", guest_count=guest_count)

@router.get("/guest-info", response_model=GuestInfo)
async def get_guest_info(current_user: dict = Depends(get_current_user)):
    guest_id = current_user["id"]
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{REDIS_SERVICE_URL}/guest/{guest_id}")
    
    if response.status_code != 200:
        raise HTTPException(status_code=404, detail="게스트 정보를 찾을 수 없습니다.")
    
    return GuestInfo(**response.json())

@router.post("/queue/{facility_id}")
async def queue_facility(facility_id: str, current_user: dict = Depends(get_current_user)):
    user_id = current_user['id']

    # Kafka를 이용해 줄서기 요청 비동기 처리
    asyncio.create_task(send_queue_request(facility_id, user_id))

    async with httpx.AsyncClient() as client:
        await client.post(f"{REDIS_SERVICE_URL}/queue", json={"facility_id": facility_id, "user_id": user_id})

    return {"message": f"Queue request for facility {facility_id} has been received."}

@router.get("/queue/{facility_id}")
async def get_facility_queue(facility_id: str, current_user: dict = Depends(get_current_user)):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{REDIS_SERVICE_URL}/queue/{facility_id}")
    return response.json()

@router.get("/top_facilities")
async def get_top_n_facilities(n: int = 10, current_user: dict = Depends(get_current_user)):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{REDIS_SERVICE_URL}/top_facilities?n={n}")
    return response.json()

@router.post("/reserve-ride/{ride_id}", response_model=RideReservation)
async def reserve_ride(ride_id: str, current_user: dict = Depends(get_current_user)):
    reservation_data = {
        "user_id": current_user['id'],
        "ride_id": ride_id
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{MESSAGE_BROKER_SERVICE_URL}/publish/ride_reservations", json=reservation_data)
    
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="예약 요청 처리 중 오류가 발생했습니다.")
    
    return RideReservation(ride_id=ride_id, reservation_time="pending", status="pending")

@router.get("/notifications", response_model=List[str])
async def get_notifications(current_user: dict = Depends(get_current_user)):
    notification_request = {
        "user_id": current_user['id']
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{MESSAGE_BROKER_SERVICE_URL}/publish/notifications", json=notification_request)
    
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="알림 요청 처리 중 오류가 발생했습니다.")
    
    return ["알림 요청이 처리 중입니다. 잠시 후 다시 확인해주요."]

@router.get("/real-time-tracking")
async def get_real_time_tracking(current_user: dict = Depends(get_current_user)):
    tracking_request = {
        "user_id": current_user['id']
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{MESSAGE_BROKER_SERVICE_URL}/publish/real_time_updates", json=tracking_request)
    
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="실시간 추적 요청 처리 중 오류가 발생했습니다.")
    
    return {"message": "실시간 추적 요청이 처리 중입니다. 잠시 후 다시 확인해주세요."}

@router.post("/exit-park")
async def exit_park(current_user: dict = Depends(get_current_user)):
    exit_request = {
        "user_id": current_user['id']
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{MESSAGE_BROKER_SERVICE_URL}/publish/exit_park", json=exit_request)
    
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="퇴장 요청 처리 중 오류가 발생했습니다.")
    
    async with httpx.AsyncClient() as client:
        await client.delete(f"{REDIS_SERVICE_URL}/guest/{current_user['id']}")
    return {"message": "공원 퇴장 요청이 처리되었습니다."}
