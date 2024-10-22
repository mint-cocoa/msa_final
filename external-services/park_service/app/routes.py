# park_service/app/routes.py
from fastapi import APIRouter, HTTPException, Depends
from .models import ParkModel, ParkRead    
from .database import get_db
from bson import ObjectId

router = APIRouter()

@router.post("/", response_model=ParkRead)
async def create_park(park: ParkModel, db=Depends(get_db)):
    existing_park = await db.parks.find_one({"name": park.name})
    if existing_park:
        raise HTTPException(status_code=400, detail="Park already exists")
    park_data = park.model_dump(by_alias=True, exclude={"id"})
    new_park = await db.parks.insert_one(park_data)
    created_park = await db.parks.find_one({"_id": new_park.inserted_id})
    return created_park

@router.get("/{park_id}", response_model=ParkRead)
async def get_park(park_id: str, db=Depends(get_db)):
    try:
        park_object_id = ObjectId(park_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid Park ID")
    
    park = await db.parks.find_one({"_id": park_object_id})
    if not park:
        raise HTTPException(status_code=404, detail="Park not found")
    return park

