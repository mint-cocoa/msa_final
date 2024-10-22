from fastapi import APIRouter, HTTPException, Depends
from .database import get_db
from bson import ObjectId
from . import models
from typing import List

router = APIRouter()

@router.post("/", response_model=models.FacilityRead)
async def create_facility(facility: models.FacilityModel, db=Depends(get_db)):
    existing_facility = await db.facilities.find_one({"name": facility.name})
    if existing_facility:
        raise HTTPException(status_code=400, detail="시설이 이미 존재합니다")
    new_facility = await db.facilities.insert_one(facility.dict(by_alias=True, exclude={"id"}))
    created_facility = await db.facilities.find_one({"_id": new_facility.inserted_id})
    return created_facility

@router.get("/{facility_id}", response_model=models.FacilityRead)
async def get_facility(facility_id: str, db=Depends(get_db)):
    facility = await db.facilities.find_one({"_id": ObjectId(facility_id)})
    if not facility:
        raise HTTPException(status_code=404, detail="시설을 찾을 수 없습니다")
    return facility

@router.get("/operating", response_model=List[models.FacilityRead])
async def get_operating_facilities(db=Depends(get_db)):
    cursor = db.facilities.find({"is_operating": True})
    facilities = await cursor.to_list(length=None)
    return facilities

