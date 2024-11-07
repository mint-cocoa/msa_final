from pydantic import BaseModel, EmailStr, ConfigDict, BeforeValidator, Field
from typing import Optional, List
from datetime import datetime
from bson import ObjectId
from typing import Annotated

PyObjectId = Annotated[str, BeforeValidator(str)]

class FacilityModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: str
    description: str
    status: str  # 'active', 'maintenance', 'closed'
    max_queue_capacity: int
    operation_start: str  # HH:MM 형식
    operation_end: str    # HH:MM 형식
    ride_duration: int    # 분 단위
    capacity_per_ride: int  # 한 번에 탑승 가능한 인원
    minimum_height: Optional[int] = None  # cm 단위

    class Config(ConfigDict):
        populate_by_name = True     
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            ObjectId: lambda oid: str(oid),
        }
        


