from fastapi import APIRouter, HTTPException, Request
from .models import ReservationCreate, ReservationCancel
from .message_handlers import ReservationMessageHandler
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/reserve/{ride_id}")
async def reserve_ride(
    ride_id: str,
    reservation: ReservationCreate
):
    try:
        message_handler = ReservationMessageHandler()
        result = await message_handler.handle_reservation_create(
            user_id=reservation.user_id,
            ride_id=ride_id,
            number_of_people=reservation.number_of_people,
            reservation_time=reservation.reservation_time
        )
        
        logger.info(f"Created reservation for user {reservation.user_id} on ride {ride_id}")
        return {
            "message": "Reservation created successfully",
            "queue_position": result["position"],
            "estimated_wait_time": result["estimated_wait_time"],
            "status": result["queue_status"]
        }
        
    except ValueError as e:
        logger.warning(f"Validation error in reserve_ride: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in reserve_ride: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create reservation")

@router.post("/cancel/{ride_id}")
async def cancel_reservation(
    ride_id: str,
    cancel_data: ReservationCancel,
    user_id: str
):
    try:
        message_handler = ReservationMessageHandler()
        if await message_handler.handle_reservation_cancel(
            user_id=user_id,
            ride_id=ride_id,
            reason=cancel_data.reason
        ):
            logger.info(f"Cancelled reservation for user {user_id} on ride {ride_id}")
            return {"message": "Reservation cancelled successfully"}
        else:
            raise HTTPException(status_code=404, detail="Reservation not found")
            
    except Exception as e:
        logger.error(f"Error in cancel_reservation: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to cancel reservation")

@router.get("/queue-status/{ride_id}")
async def get_queue_status(
    ride_id: str,
    user_id: str
):
    try:
        message_handler = ReservationMessageHandler()
        status = await message_handler.get_queue_status(
            ride_id=ride_id,
            user_id=user_id
        )
        return status
        
    except ValueError as e:
        logger.warning(f"Validation error in get_queue_status: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in get_queue_status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get queue status")
