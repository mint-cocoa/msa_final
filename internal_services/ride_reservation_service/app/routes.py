from fastapi import APIRouter, HTTPException, Depends
from .dependencies import get_current_user
import aio_pika
import json
import httpx
import os

router = APIRouter()

REDIS_SERVICE_URL = os.getenv("REDIS_SERVICE_URL", "http://redis-service:8000")

@router.post("/reserve/{ride_id}")
async def reserve_ride(ride_id: str, current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    
    # RabbitMQ에 예약 요청 메시지 발행
    message = aio_pika.Message(
        body=json.dumps({"user_id": user_id, "ride_id": ride_id}).encode()
    )
    await router.app.state.rabbitmq_channel.default_exchange.publish(
        message, routing_key='ride_reservations'
    )
    
    return {"message": f"User {user_id} reservation request for ride {ride_id} has been sent."}

@router.get("/queue_position/{ride_id}")
async def get_position(ride_id: str, current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{REDIS_SERVICE_URL}/queue_position/{ride_id}/{user_id}")
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.json().get("detail"))
        return response.json()

@router.post("/complete_ride/{ride_id}")
async def complete_ride(ride_id: str, current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{REDIS_SERVICE_URL}/complete_ride/{ride_id}/{user_id}")
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.json().get("detail"))
        return response.json()

# 테스트 엔드포인트 추가
@router.get("/dev/reserve/{user_id}")
async def test_endpoint(user_id: str):
    
    # RabbitMQ에 예약 요청 메시지 발행
    message = aio_pika.Message(
        body=json.dumps({"user_id": user_id, "ride_id": "1234"}).encode()
    )
    await router.app.state.rabbitmq_channel.default_exchange.publish(
        message, routing_key='ride_reservations'
    )
    return {"message": f"User {user_id} reservation request has been sent."}

@router.get("/dev/position/{ride_id}")
async def test_position_endpoint(ride_id: str):
    return {"message": f"Ride {ride_id} position request has been sent."}

@router.post("/dev/complete/{ride_id}")
async def test_complete_endpoint(ride_id: str):
    return {"message": f"Ride {ride_id} completion request has been sent."} 
