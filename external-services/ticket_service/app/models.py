from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CreateTicketForm(BaseModel):
    user_id: str = Field(..., title="사용자 ID", description="티켓을 구매하는 사용자의 고유 식별자")
    park_id: str = Field(..., title="공원 ID", description="구매할 공원의 고유 식별자")
    ticket_type_name: str = Field(..., title="티켓 유형 이름", description="구매할 티켓 유형의 이름")

class TicketResponse(BaseModel):
    token: str 
    
    class Config:
        orm_mode = True

class User(BaseModel):
    id: str
    username: str
    email: str

class Park(BaseModel):
    id: str
    name: str
    location: str

class Facility(BaseModel):
    id: str
    name: str
    park_id: str

class Ticket(BaseModel):
    id: str
    user_id: str
    park_id: str
    ticket_type_name: str
    allowed_facilities: List[str]
    purchase_date: datetime
    amount: float
    available_date: str
    used: bool
    used_at: Optional[datetime] = None
