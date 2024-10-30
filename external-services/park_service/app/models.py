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
    status: str
    
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

class ParkStructureNode(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    park_id: PyObjectId
    ticket_type_id: PyObjectId
    facility_id: PyObjectId
    access_level: str = "normal"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={
            datetime: lambda dt: dt.isoformat(),
            ObjectId: lambda oid: str(oid),
        }
    )