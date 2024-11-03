from fastapi import APIRouter, HTTPException, Request, Depends
from .models import ReservationCreate, ReservationResponse, ReservationCancel
from .message_handlers import ReservationMessageHandler
from datetime import datetime

router = APIRouter()

async def get_message_handler(request: Request) -> ReservationMessageHandler:
    return ReservationMessageHandler(request.app.state.rabbitmq_publisher)

@router.post("/reserve/{ride_id}", response_model=ReservationResponse)
async def reserve_ride(
    ride_id: str, 
    reservation: ReservationCreate,
    message_handler: ReservationMessageHandler = Depends(get_message_handler)
):
    position = await message_handler.handle_reservation_create(
        user_id=reservation.user_id,
        ride_id=ride_id,
        number_of_people=reservation.number_of_people,
        reservation_time=reservation.reservation_time
    )
    
    return ReservationResponse(
        id=f"{reservation.user_id}:{ride_id}",
        ride_id=ride_id,
        user_id=reservation.user_id,
        number_of_people=reservation.number_of_people,
        reservation_time=reservation.reservation_time,
        status="pending",
        position=position,
        created_at=datetime.utcnow()
    )

@router.post("/cancel/{ride_id}")
async def cancel_ride_reservation(
    ride_id: str,
    user_id: str,
    cancel_data: ReservationCancel,
    message_handler: ReservationMessageHandler = Depends(get_message_handler)
):
    if not await message_handler.handle_reservation_cancel(
        user_id=user_id,
        ride_id=ride_id,
        reason=cancel_data.reason
    ):
        raise HTTPException(status_code=404, detail="Reservation not found")
    
    return {"message": "Reservation cancelled successfully"}

@router.get("/queue-status/{ride_id}")
async def get_queue_status(
    ride_id: str,
    message_handler: ReservationMessageHandler = Depends(get_message_handler)
):
    return await message_handler.handle_queue_status_update(ride_id)
