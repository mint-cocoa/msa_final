from pydantic import BaseModel

class FacilityCreate(BaseModel):
    name: str
    type: str

class FacilityResponse(BaseModel):
    id: int
    name: str
    type: str

    class Config:
        orm_mode = True
