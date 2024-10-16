from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class TicketCreate(BaseModel):
    user_id: str
    park_id: str
    facility_id: str
    status: Optional[str] = Field(default="pending")

class TicketRead(BaseModel):
    id: str
    user_id: str
    park_id: str
    facility_id: str
    status: str
    created_at: datetime
    updated_at: datetime

class TicketUpdate(BaseModel):
    status: Optional[str]