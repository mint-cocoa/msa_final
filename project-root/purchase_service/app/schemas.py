from pydantic import BaseModel, EmailStr, condecimal
from typing import List
from datetime import datetime

class TicketPurchaseItem(BaseModel):
    ticket_type_id: str
    quantity: int

class PurchaseRequest(BaseModel):
    user_id: int
    items: List[TicketPurchaseItem]

class PurchaseResponse(BaseModel):
    purchase_id: str
    user_id: int
    items: List[TicketPurchaseItem]
    total_price: float
    purchased_at: datetime