from pydantic import BaseModel, Field, ConfigDict, BeforeValidator
from typing import Optional, List, Annotated
from datetime import datetime
from bson import ObjectId

PyObjectId = Annotated[str, BeforeValidator(str)]

class TreeNode(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    node_type: str  # "park" or "facility" or "ticket_type"
    reference_id: PyObjectId
    name: str
    parent_id: Optional[PyObjectId] = None
    children: List['TreeNode'] = []
    level: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={
            datetime: lambda dt: dt.isoformat(),
            ObjectId: str
        }
    )

# 재귀적 참조를 위한 업데이트
TreeNode.model_rebuild()

class NodeCreate(BaseModel):
    node_type: str
    reference_id: str
    name: str
    parent_id: Optional[str] = None

    model_config = ConfigDict(
        populate_by_name=True
    )

