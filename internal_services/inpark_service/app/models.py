from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UseTicketResponse(BaseModel):
    message: str
    guest_count: int

class GuestInfo(BaseModel):
    token: str
    entered_at: datetime
    user_id: str
    park_id: str

class RideReservation(BaseModel):
    ride_id: str
    reservation_time: datetime
    status: str
