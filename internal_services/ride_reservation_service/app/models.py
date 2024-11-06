from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ReservationCreate(BaseModel):
    ride_id: str
    user_id: str
    number_of_people: int
    reservation_time: datetime

class ReservationResponse(BaseModel):
    id: str
    ride_id: str
    user_id: str
    number_of_people: int
    reservation_time: datetime
    status: str  # 'pending', 'confirmed', 'cancelled'
    created_at: datetime
    
class ReservationCancel(BaseModel):
    reason: Optional[str] = None 