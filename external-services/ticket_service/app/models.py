from pydantic import BaseModel, Field
from typing import Optional


class CreateTicketForm(BaseModel):
    user_id: str = Field(..., title="사용자 ID", description="티켓을 구매하는 사용자의 고유 식별자")
    park_id: str = Field(..., title="공원 ID", description="구매할 공원의 고유 식별자")
    ticket_type_name: str = Field(..., title="티켓 유형 이름", description="구매할 티켓 유형의 이름")

class TicketResponse(BaseModel):
    token: str 
    
    class Config:
        orm_mode = True
