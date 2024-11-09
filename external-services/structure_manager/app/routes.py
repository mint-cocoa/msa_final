from fastapi import APIRouter, HTTPException, Request
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime
from bson import ObjectId
import logging
from .database import get_db

router = APIRouter()

@router.get("/parks/{park_id}/facilities")
async def get_park_facilities(park_id: str, request: Request):
    try:
        db = await get_db()
        
        # 공원 노드에서 시설물 ID 목록 조회
        park_node = await db.nodes.find_one({
            "type": "park",
            "reference_id": ObjectId(park_id)
        })
        if not park_node:
            raise HTTPException(status_code=404, detail="Park not found")
            
        facilities = []
        for facility_id in park_node.get("facilities", []):
            facility = await db.facilities.find_one({"_id": facility_id})
            if facility:
                facility["_id"] = str(facility["_id"])
                facilities.append(facility)
                
        return facilities
    except Exception as e:
        logging.error(f"Failed to get park facilities: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 
    
@router.get("/health")
async def health():
    return {"status": "ok"}
    