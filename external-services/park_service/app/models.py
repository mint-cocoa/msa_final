from pydantic import BaseModel, EmailStr, ConfigDict ,BeforeValidator ,Field
from typing import Optional
from datetime import datetime
from bson import ObjectId
from typing import Annotated ,List
PyObjectId = Annotated[str, BeforeValidator(str)]

class TicketTypeModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: str
    description: str
    price: float
    
    class Config(ConfigDict):
        populate_by_name = True
        arbitrary_types_allowed=True
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            ObjectId: lambda oid: str(oid),
        }

class ParkModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: str
    location: str
    description: str
    ticket_types: List[TicketTypeModel] = []
    
    class Config(ConfigDict):
        populate_by_name = True
        arbitrary_types_allowed=True
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            ObjectId: lambda oid: str(oid),
        }

class ParkRead(ParkModel):
    name: str
    location: str
    description: str
    ticket_types: List[TicketTypeModel] = []

