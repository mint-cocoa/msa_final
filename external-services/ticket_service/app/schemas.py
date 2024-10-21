from pydantic import BaseModel

class CreateTicketForm(BaseModel):
    user_id: str
    park_ticket_id: str
    available_date: str

class TicketResponse(BaseModel):
    ticket_id: str
    message: str

class TicketUseResponse(BaseModel):
    message: str
    access_token: str
    token_type: str
