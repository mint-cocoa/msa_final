from fastapi import APIRouter
from .models import ParkCreate, ParkRead
from .services import create_park_with_tickets

router = APIRouter()

@router.post("/parks/", response_model=ParkRead)
def create_park(park: ParkCreate):
    created_park = create_park_with_tickets(park)
    return created_park.dict(by_alias=True)
