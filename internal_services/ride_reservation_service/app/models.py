from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class ReservationCreate(BaseModel):
    number_of_people: int = Field(gt=0, le=10, description="예약할 인원 수 (1-10명)")
    reservation_time: datetime = Field(description="예약 희망 시간")
    user_id: str = Field(description="사용자 ID")

class ReservationResponse(BaseModel):
    id: str
    user_id: str
    number_of_people: int
    reservation_time: datetime
    status: str  # 'pending', 'confirmed', 'cancelled'
    created_at: datetime
    
class ReservationCancel(BaseModel):
    reason: Optional[str] = None