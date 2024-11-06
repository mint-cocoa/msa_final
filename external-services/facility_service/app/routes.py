from fastapi import APIRouter, HTTPException, Depends, Request
from .models import FacilityModel
from .database import get_db
from .crud import (
    create_facility, update_facility, delete_facility, get_facility,
    get_facilities
)
import httpx
import os
from datetime import datetime
from bson import ObjectId

STRUCTURE_MANAGER_URL = os.getenv('STRUCTURE_MANAGER_URL', 'http://structure-manager:8000')
router = APIRouter()

@router.post("/facilities/create")
async def create_facility_endpoint(facility: FacilityModel, request: Request):
    db = await get_db()
    facility_id = await create_facility(db, facility)
    
    # Structure Manager에 노드 생성 요청
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{STRUCTURE_MANAGER_URL}/api/nodes",
            json={
                "node_type": "facility",
                "reference_id": str(facility_id),
                "name": facility.name,
                "parent_id": str(facility.park_id)
            }
        )
        if response.status_code != 200:
            # 시설 생성 롤백
            await db.facilities.delete_one({"_id": ObjectId(facility_id)})
            raise HTTPException(status_code=400, detail="Failed to create facility structure")
    
    return {"id": str(facility_id)}

@router.get("/facilities/{facility_id}")
async def get_facility_endpoint(facility_id: str):
    db = await get_db()
    facility = await get_facility(db, facility_id)
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    
    # Structure Manager에서 하위 트리 정보 가져오기
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{STRUCTURE_MANAGER_URL}/api/nodes/{facility_id}/subtree"
        )
        if response.status_code == 200:
            structure_info = response.json()
            facility["structure"] = structure_info
    
    return facility

@router.get("/facilities/park/{park_id}")
async def get_park_facilities(park_id: str):
    db = await get_db()
    facilities = await get_facilities(db, park_id)
    
    # Structure Manager에서 공원의 전체 구조 가져오기
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{STRUCTURE_MANAGER_URL}/api/nodes/{park_id}/subtree"
        )
        if response.status_code == 200:
            structure_tree = response.json()
            return {
                "facilities": facilities,
                "structure": structure_tree
            }
    
    return {"facilities": facilities}
