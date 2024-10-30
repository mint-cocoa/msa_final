from typing import Optional, List, ObjectId
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class AccessControl(BaseModel):
    id: Optional[ObjectId] = Field(alias="_id", default=None)
    ticket_type_id: ObjectId
    park_id: ObjectId
    facility_ids: List[ObjectId]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }
    ) 