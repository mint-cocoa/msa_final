from pydantic import BaseModel, EmailStr, ConfigDict ,BeforeValidator ,Field
from typing import Optional
from datetime import datetime
from bson import ObjectId
from typing import Annotated ,List

PyObjectId = Annotated[str, BeforeValidator(str)]

class FacilityModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: str
    is_operating: bool
    description: str
    open_time: datetime
    close_time: datetime    
    max_queue_capacity: int
    
    class Config(ConfigDict):
        populate_by_name = True     
        arbitrary_types_allowed=True
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            ObjectId: lambda oid: str(oid),
        }

class FacilityRead(FacilityModel):
    id: PyObjectId
    created_at: datetime
    updated_at: datetime

class FacilityCreate(FacilityModel):
    pass

class FacilityUpdate(FacilityModel):
    pass
