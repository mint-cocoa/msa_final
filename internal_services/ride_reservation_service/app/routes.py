from fastapi import APIRouter, HTTPException, Depends
from .dependencies import get_current_user
from .operations import add_to_queue, get_queue_position, cancel_reservation, get_ride_stats
from .models import ReservationCreate, ReservationResponse, ReservationCancel
import aio_pika
import json
from datetime import datetime

router = APIRouter()

@router.post("/reserve/{ride_id}", response_model=ReservationResponse)
async def reserve_ride(
    ride_id: str, 
    reservation: ReservationCreate,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["user_id"]
    
    # Redis를 사용하여 줄서기 큐에 사용자 추가
    position = await add_to_queue(
        redis_client,
        ride_id,
        user_id,
        reservation.number_of_people,
        reservation.reservation_time
    )
    
    # RabbitMQ에 예약 요청 메시지 발행
    message = aio_pika.Message(
        body=json.dumps({
            "user_id": user_id,
            "ride_id": ride_id,
            "position": position,
            "number_of_people": reservation.number_of_people,
            "reservation_time": reservation.reservation_time.isoformat()
        }).encode()
    )
    await router.app.state.rabbitmq_channel.default_exchange.publish(
        message, routing_key='ride_reservations'
    )
    
    return ReservationResponse(
        id=str(position),
        ride_id=ride_id,
        user_id=user_id,
        number_of_people=reservation.number_of_people,
        reservation_time=reservation.reservation_time,
        status="pending",
        created_at=datetime.utcnow()
    )

@router.get("/queue_position/{ride_id}")
async def get_position(ride_id: str, current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    position = await get_queue_position(redis_client, ride_id, user_id)
    if position is None:
        raise HTTPException(status_code=404, detail="User not in queue")
    return {"ride_id": ride_id, "position": position}

@router.post("/cancel/{ride_id}")
async def cancel_ride_reservation(
    ride_id: str,
    cancel_data: ReservationCancel,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["user_id"]
    cancelled = await cancel_reservation(redis_client, ride_id, user_id)
    if not cancelled:
        raise HTTPException(status_code=404, detail="Reservation not found")
    
    # RabbitMQ에 취소 메시지 발행
    message = aio_pika.Message(
        body=json.dumps({
            "user_id": user_id,
            "ride_id": ride_id,
            "action": "cancel",
            "reason": cancel_data.reason
        }).encode()
    )
    await router.app.state.rabbitmq_channel.default_exchange.publish(
        message, routing_key='ride_cancellations'
    )
    
    return {"message": "Reservation cancelled successfully"}

@router.get("/stats/{ride_id}")
async def get_ride_statistics(ride_id: str):
    stats = await get_ride_stats(redis_client, ride_id)
    return stats
