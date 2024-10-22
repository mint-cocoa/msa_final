# user_service/app/schemas.py
from pydantic import BaseModel, EmailStr, ConfigDict ,BeforeValidator ,Field
from typing import Optional
from datetime import datetime
from bson import ObjectId
from typing import Annotated

PyObjectId = Annotated[str, BeforeValidator(str)]

class UserModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    email: EmailStr
    password: str
    is_admin: Optional[bool] = False
    created_at: datetime
    updated_at: datetime
    
    class Config(ConfigDict):
        populate_by_name = True
        arbitrary_types_allowed=True
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            ObjectId: lambda oid: str(oid),
        }
    
class UserCreate(BaseModel):
    email: EmailStr
    password: str   
    is_admin: Optional[bool] = False
    created_at: datetime
    updated_at: datetime
    
class UserRead(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    email: EmailStr
    is_admin: Optional[bool] = False
    created_at: datetime
    updated_at: datetime

class UserLogin(BaseModel):
    email: EmailStr
    password: str