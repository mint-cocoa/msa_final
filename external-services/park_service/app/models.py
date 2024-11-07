from datetime import datetime
from typing import Annotated, Optional, List
from pydantic import BaseModel, ConfigDict, BeforeValidator, Field
from bson import ObjectId

# ObjectId 변환을 위한 커스텀 타입
PyObjectId = Annotated[str, BeforeValidator(str)]

class MongoBaseModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {
            datetime: lambda dt: dt.isoformat(),
            ObjectId: lambda oid: str(oid),
        }
    }

# 사용 예시
class TicketTypeModel(MongoBaseModel):
    name: str
    description: str
    price: float

class ParkModel(MongoBaseModel):
    name: str
    location: str
    description: str
    ticket_types: List[TicketTypeModel]
    status: str
    
class ParkUpdateModel(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    ticket_types: Optional[List[TicketTypeModel]] = None
    status: Optional[str] = None
