from pydantic import BaseModel

class ParkCreate(BaseModel):
    name: str
    location: str

class ParkResponse(BaseModel):
    id: int
    name: str
    location: str

    class Config:
        orm_mode = True
