from fastapi import APIRouter, HTTPException, Depends, Request
from .database import get_db
from bson import ObjectId
from . import models
from typing import List
from common.publisher import publish_structure_update

router = APIRouter()

@router.post("/", response_model=models.FacilityModel)
async def create_facility(facility: models.FacilityModel, request: Request, db=Depends(get_db)):
    existing_facility = await db.facilities.find_one({"name": facility.name})
    if existing_facility:
        raise HTTPException(status_code=400, detail="시설이 이미 존재합니다")
    new_facility = await db.facilities.insert_one(facility.dict(by_alias=True, exclude={"id"}))
    created_facility = await db.facilities.find_one({"_id": new_facility.inserted_id})
    
    # 구조 업데이트 메시지 발행
    await publish_structure_update(
        request.app.state.rabbitmq_channel,
        {
            "action": "create",
            "node_type": "facility",
            "reference_id": str(new_facility.inserted_id),
            "name": facility.name
        }
    )
    
    return created_facility

@router.get("/{facility_id}", response_model=models.FacilityModel)
async def get_facility(facility_id: str, db=Depends(get_db)):
    facility = await db.facilities.find_one({"_id": ObjectId(facility_id)})
    if not facility:
        raise HTTPException(status_code=404, detail="시설을 찾을 수 없습니다")
    return facility

@router.get("/operating/all", response_model=List[models.FacilityModel])
async def get_operating_facilities(db=Depends(get_db)):
    facilities = await db.facilities.find({"is_operating": True}).to_list(1000)
    return facilities

