from pydantic import BaseModel, Field
from typing import Optional

class CreateTicketForm(BaseModel):
    user_id: str = Field(..., title="사용자 ID", description="티켓을 구매하는 사용자의 고유 식별자")
    park_ticket_id: str = Field(..., title="공원 티켓 ID", description="구매할 공원 티켓의 고유 식별자")

class TicketResponse(BaseModel):
    user_id: str
    park_id: str
    park_ticket_data: dict
    purchase_date: str
    amount: float
    token: str 

    class Config:
        orm_mode = True
