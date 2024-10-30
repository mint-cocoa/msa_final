from fastapi import APIRouter, HTTPException, Depends, Request
from .models import ReservationCreate, ReservationResponse, ReservationCancel
from .database import get_db
from .crud import (
    create_reservation,
    get_reservation,
    update_reservation_status,
    cancel_reservation
)
from datetime import datetime

router = APIRouter()

@router.post("/reserve/{ride_id}", response_model=ReservationResponse)
async def reserve_ride(
    ride_id: str, 
    reservation: ReservationCreate,
    request: Request
):
    db = await get_db()
    reservation_id = await create_reservation(db, reservation)
    
    # Redis를 사용하여 줄서기 큐에 사용자 추가
    position = await add_to_queue(
        request.app.state.redis,
        ride_id,
        reservation.user_id,
        reservation.number_of_people,
        reservation.reservation_time
    )
    
    # RabbitMQ를 통해 예약 이벤트 발행
    await request.app.state.rabbitmq_publisher.publish_reservation_event(
        action="create",
        user_id=reservation.user_id,
        ride_id=ride_id,
        position=position,
        number_of_people=reservation.number_of_people,
        reservation_time=reservation.reservation_time
    )
    
    return ReservationResponse(
        id=str(reservation_id),
        ride_id=ride_id,
        user_id=reservation.user_id,
        number_of_people=reservation.number_of_people,
        reservation_time=reservation.reservation_time,
        status="pending",
        created_at=datetime.utcnow()
    )

@router.post("/cancel/{reservation_id}")
async def cancel_ride_reservation(
    reservation_id: str,
    cancel_data: ReservationCancel,
    request: Request
):
    db = await get_db()
    reservation = await get_reservation(db, reservation_id)
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    
    success = await cancel_reservation(db, reservation_id)
    if success:
        await request.app.state.rabbitmq_publisher.publish_cancellation_event(
            user_id=reservation["user_id"],
            ride_id=reservation["ride_id"],
            reason=cancel_data.reason
        )
        return {"message": "Reservation cancelled successfully"}
    raise HTTPException(status_code=400, detail="Failed to cancel reservation")
