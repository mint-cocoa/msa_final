from fastapi import APIRouter, HTTPException, Depends
from .dependencies import get_current_user
from .operations import add_to_queue, get_queue_position, remove_from_queue
import aio_pika
import json

router = APIRouter()

@router.post("/reserve/{ride_id}")
async def reserve_ride(ride_id: str, current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    
    # Redis를 사용하여 줄서기 큐에 사용자 추가
    position = await add_to_queue(ride_id, user_id)
    
    # RabbitMQ에 예약 요청 메시지 발행
    message = aio_pika.Message(
        body=json.dumps({"user_id": user_id, "ride_id": ride_id, "position": position}).encode()
    )
    await router.app.state.rabbitmq_channel.default_exchange.publish(
        message, routing_key='ride_reservations'
    )
    
    return {"message": f"User {user_id} added to queue for ride {ride_id}", "position": position}

@router.get("/queue_position/{ride_id}")
async def get_position(ride_id: str, current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    position = await get_queue_position(ride_id, user_id)
    if position is None:
        raise HTTPException(status_code=404, detail="User not in queue")
    return {"ride_id": ride_id, "position": position}

@router.post("/complete_ride/{ride_id}")
async def complete_ride(ride_id: str, current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    removed = await remove_from_queue(ride_id, user_id)
    if not removed:
        raise HTTPException(status_code=404, detail="User not in queue")
    return {"message": f"User {user_id} removed from queue for ride {ride_id}"}
