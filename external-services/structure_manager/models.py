from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict
from bson import ObjectId
from datetime import datetime

class ParkStructureTreeNode(BaseModel):
    id: Optional[ObjectId] = Field(alias="_id", default=None)
    parent_id: Optional[ObjectId] = None
    node_type: str  # "park", "ticket_type", "facility"
    reference_id: ObjectId
    name: str
    level: int = 0
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

class TicketTypeAccess(BaseModel):
    id: Optional[ObjectId] = Field(alias="_id", default=None)
    ticket_type_id: ObjectId
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

class NodeCreate(BaseModel):
    parent_id: Optional[str] = None
    node_type: str
    reference_id: str
    name: str


