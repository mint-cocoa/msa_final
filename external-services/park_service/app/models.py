from pydantic import BaseModel, EmailStr, ConfigDict, BeforeValidator, Field
from typing import Optional, List, Annotated
from datetime import datetime
from bson import ObjectId
from typing import Annotated

PyObjectId = Annotated[str, BeforeValidator(str)]

class TicketTypeModel(BaseModel):
    name: str
    description: str
    price: float
    allowed_facilities: List[PyObjectId] = []  # ObjectId 문자열 리스트로 변경

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={
            datetime: lambda dt: dt.isoformat(),
            ObjectId: lambda oid: str(oid),
        }
    )

class ParkModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: str
    location: str
    description: str
    ticket_types: List[TicketTypeModel] = []
    
    class Config(ConfigDict):
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            ObjectId: lambda oid: str(oid),
        }
        
class ParkCreate(BaseModel):
    name: str
    location: str
    description: str
    ticket_types: List[TicketTypeModel] = []
    

class ParkRead(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: str
    location: str
    description: str
    ticket_types: List[TicketTypeModel] = []

    class Config(ConfigDict):
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            ObjectId: lambda oid: str(oid),
        }
