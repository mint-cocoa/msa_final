from datetime import datetime
from typing import Annotated, Optional, List
from pydantic import BaseModel, ConfigDict, BeforeValidator, Field
from bson import ObjectId

PyObjectId = Annotated[str, BeforeValidator(str)]

class NodeModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    node_type: str
    reference_id: PyObjectId  # parks 컬렉션의 _id
    name: str
    facilities: List[PyObjectId] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={
            datetime: lambda dt: dt.isoformat(),
            ObjectId: lambda oid: str(oid),
        }
    )

    class Collection:
        name = "nodes"
