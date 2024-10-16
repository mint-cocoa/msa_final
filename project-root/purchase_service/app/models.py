from pydantic import BaseModel, EmailStr, ConfigDict ,BeforeValidator ,Field
from datetime import datetime
from typing import Optional
from typing import Annotated

PyObjectId = Annotated[str, BeforeValidator(str)]

class PurchaseModel(BaseModel):  
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    purchase_user_id: int
    purchase_ticket_park_id: int
    purchase_ticket_type_field: str
    purchase_ticket_quantity: int
    purchase_ticket_purchased_at: datetime

    class Config(ConfigDict):
        populate_by_name = True
        arbitrary_types_allowed=True
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            ObjectId: lambda oid: str(oid),
        }


    
class UserCreate(UserModel):
    pass

class UserRead(UserModel):
    password: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str