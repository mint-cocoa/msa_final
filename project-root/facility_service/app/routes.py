from fastapi import APIRouter, HTTPException, Depends
from .utils import get_database
from bson import ObjectId
from . import utils, models
from .database import get_db
router = APIRouter()

@router.post("/facilities", response_model=models.FacilityRead)
async def create_facility(facility: models.FacilityModel, db=Depends(get_db)):
    existing_facility = await utils.get_facility_by_name(db, facility.name)
    if existing_facility:
        raise HTTPException(status_code=400, detail="Facility already exists")
    new_facility = await db.facilities.insert_one(facility.model_dump(by_alias=True, exclude=["id"]))
    created_facility = await db.facilities.find_one({"_id": new_facility.inserted_id})
    return created_facility

@router.get("/facilities/{facility_id}", response_model=models.FacilityRead)
async def get_facility(facility_id: str, db=Depends(get_db)):
    facility = await utils.get_facility_by_id(db, facility_id)
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    return facility
