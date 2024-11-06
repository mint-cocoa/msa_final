from datetime import datetime
from typing import Annotated, Optional
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
    status: str
    