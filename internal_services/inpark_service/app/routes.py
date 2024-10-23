from fastapi import APIRouter, HTTPException, Depends
from .database import redis_client
from .models import UseTicketResponse, GuestInfo, RideReservation
from .dependencies import get_current_user
from .redis_client import add_to_queue, get_queue, queue_length, get_top_facilities, remove_facility
from .kafka_producer import send_queue_request
import httpx
import os
from typing import List
import asyncio

router = APIRouter()

TICKET_SERVICE_URL = os.getenv("TICKET_SERVICE_URL", "http://ticket-service:8000")
MESSAGE_BROKER_SERVICE_URL = os.getenv("MESSAGE_BROKER_SERVICE_URL", "http://message_broker_service:8000")

@router.post("/enter-park/{token}", response_model=UseTicketResponse)
async def enter_park(token: str):
    # 기존 코드 유지
    ...

@router.get("/guest-info", response_model=GuestInfo)
async def get_guest_info(current_user: dict = Depends(get_current_user)):
    # 기존 코드 유지
    ...

@router.post("/queue/{facility_id}")
async def queue_facility(facility_id: str, current_user: dict = Depends(get_current_user)):
    user_id = current_user['id']

    # Kafka를 이용해 줄서기 요청 비동기 처리
    asyncio.create_task(send_queue_request(facility_id, user_id))

    return {"message": f"Queue request for facility {facility_id} has been received."}

@router.get("/queue/{facility_id}")
async def get_facility_queue(facility_id: str, current_user: dict = Depends(get_current_user)):
    queue = await get_queue(facility_id)
    return {"facility_id": facility_id, "queue": queue, "length": len(queue)}

@router.get("/top_facilities")
async def get_top_n_facilities(n: int = 10, current_user: dict = Depends(get_current_user)):
    top_facilities = await get_top_facilities(n)
    return {"top_facilities": top_facilities}

@router.get("/notifications", response_model=List[str])
async def get_notifications(current_user: dict = Depends(get_current_user)):
    # 기존 코드 유지
    ...

@router.get("/real-time-tracking")
async def get_real_time_tracking(current_user: dict = Depends(get_current_user)):
    # 기존 코드 유지
    ...

@router.post("/exit-park")
async def exit_park(current_user: dict = Depends(get_current_user)):
    # 기존 코드 유지
    ...
