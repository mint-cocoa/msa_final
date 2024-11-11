from fastapi import APIRouter, HTTPException, Request, Depends
from .models import FacilityModel
import logging
from motor.motor_asyncio import AsyncIOMotorDatabase
from .database import get_db
from typing import Dict, Any
import asyncio
logger = logging.getLogger(__name__)
router = APIRouter()

async def wait_for_response(event_handler, timeout: int = 30) -> Dict[str, Any]:
    """응답을 기다리는 유틸리티 함수"""
    start_time = asyncio.get_event_loop().time()
    while asyncio.get_event_loop().time() - start_time < timeout:
        if event_handler.latest_response:
            response = event_handler.latest_response
            event_handler.latest_response = None  # 응답 초기화
            return response
        await asyncio.sleep(0.1)
    raise HTTPException(status_code=408, detail="Response timeout")

@router.post("/parks/{park_id}/facilities")
async def create_facility_endpoint(park_id: str, facility: FacilityModel, request: Request):
    try:
       
        await request.app.state.publisher.create_facility({
            "park_id": park_id,
            "data": facility.dict()
        })
      
        response = await wait_for_response(request.app.state.consumer.event_mapper.event_handler)
        logger.info(f"Response: {response}")
        if response.get("status") == "success": 
            return {
                "status": "success",
                "message": "Facility created successfully",
                "facility_id": response.get("_id"),
                "data": {
                    **facility.dict(),
                    "park_id": park_id
                }
            }
        else:
            raise HTTPException(status_code=400, detail=response.get("error", "Failed to create facility")) 
    except Exception as e:
        logger.error(f"Failed to create facility: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/parks/{park_id}/facilities/{facility_id}")
async def update_facility_endpoint(
    park_id: str, 
    facility_id: str, 
    facility: FacilityModel, 
    request: Request
):
    try:
        logger.info(f"Updating facility {facility_id} in park {park_id}")
        await request.app.state.publisher.update_facility({
            "reference_id": facility_id,
            "park_id": park_id,
            "data": facility.dict()
        })
        return {"status": "success", "message": "Facility update request sent"}
    except Exception as e:
        logger.error(f"Failed to update facility: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/parks/{park_id}/facilities/{facility_id}")
async def delete_facility_endpoint(park_id: str, facility_id: str, request: Request):
    try:
        logger.info(f"Deleting facility {facility_id} from park {park_id}")
        await request.app.state.publisher.delete_facility({
            "reference_id": facility_id,
            "park_id": park_id
        })
        return {"status": "success", "message": "Facility deletion request sent"}
    except Exception as e:
        logger.error(f"Failed to delete facility: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/parks/{park_id}/facilities/{facility_id}")
async def get_facility_endpoint(
    park_id: str, 
    facility_id: str, 
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    try:
        logger.info(f"Fetching facility {facility_id} from park {park_id}")
        facility = await db.facilities.find_one({"_id": facility_id, "park_id": park_id})
        if not facility:
            raise HTTPException(status_code=404, detail="Facility not found")
        facility["_id"] = str(facility["_id"])
        return {"status": "success", "data": facility}
    except Exception as e:
        logger.error(f"Failed to get facility: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/parks/{park_id}/facilities")
async def get_park_facilities_endpoint(
    park_id: str, 
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    try:
        logger.info(f"Fetching all facilities for park {park_id}")
        facilities = await db.facilities.find({"park_id": park_id}).to_list(None)
        for facility in facilities:
            facility["_id"] = str(facility["_id"])
        return {
            "status": "success",
            "data": {
                "facilities": facilities,
                "total": len(facilities)
            }
        }
    except Exception as e:
        logger.error(f"Failed to get park facilities: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/facilities/active")
async def get_active_facilities(
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    try:
        logger.info("Fetching active facilities")
        facilities = await db.facilities.find({"status": "active"}).to_list(None)
        for facility in facilities:
            facility["_id"] = str(facility["_id"])
        return {
            "status": "success",
            "data": {
                "facilities": facilities,
                "total": len(facilities)
            }
        }
    except Exception as e:
        logger.error(f"Failed to get active facilities: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))