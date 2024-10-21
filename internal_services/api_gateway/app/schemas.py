from pydantic import BaseModel
from datetime import datetime

class UseTicketResponse(BaseModel):
    message: str
    user_id: str
    park_id: str

class ReservationRequest(BaseModel):
    reservation_time: datetime
