# park_service/app/routes.py
from fastapi import APIRouter, HTTPException, Request, Depends
from .models import ParkModel
from .database import get_db
import logging
import asyncio
from typing import Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase

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

@router.post("/parks/create")
async def create_park_endpoint(park: ParkModel, request: Request):
    try:
        # 메시지 발행
        await request.app.state.publisher.create_park({
            "action": "create",
            "node_type": "park",
            "name": park.name,
            "data": park.dict()
        })
        
        # 응답 대기
        response = await wait_for_response(request.app.state.consumer.event_mapper.event_handler)
        
        if response.get("status") == "success":
            return {"message": "Park created successfully", "data": response.get("data")}
        else:
            raise HTTPException(status_code=400, detail=response.get("error", "Failed to create park"))
            
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="Request timeout")
    except Exception as e:
        logging.error(f"Failed to create park: {e}")
        raise HTTPException(status_code=500, detail="Failed to create park")

@router.post("/parks/{park_id}/update")
async def update_park_endpoint(park_id: str, park: ParkModel, request: Request):
    try:
        await request.app.state.publisher.publish_structure_update({
            "action": "update",
            "node_type": "park",
            "reference_id": park_id,
            "name": park.name,
            "data": park.dict()
        })
        
        # 응답 대기
        response = await wait_for_response(request.app.state.consumer.event_mapper.event_handler)
        
        if response.get("status") == "success":
            return {"message": "Park updated successfully", "data": response.get("data")}
        else:
            raise HTTPException(status_code=400, detail=response.get("error", "Failed to update park"))
            
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="Request timeout")
    except Exception as e:
        logging.error(f"Failed to update park: {e}")
        raise HTTPException(status_code=500, detail="Failed to update park")

@router.post("/parks/{park_id}/delete")
async def delete_park_endpoint(park_id: str, request: Request):
    try:
        await request.app.state.publisher.publish_structure_update({
            "action": "delete",
            "node_type": "park",
            "reference_id": park_id
        })
        
        # 응답 대기
        response = await wait_for_response(request.app.state.consumer.event_mapper.event_handler)
        
        if response.get("status") == "success":
            return {"message": "Park deleted successfully"}
        else:
            raise HTTPException(status_code=400, detail=response.get("error", "Failed to delete park"))
            
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="Request timeout")
    except Exception as e:
        logging.error(f"Failed to delete park: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete park")

@router.get("/parks/ids")
async def get_park_ids_endpoint(db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        # Get all park IDs from database
        cursor = db.parks.find({}, {"_id": 1})
        park_ids = [str(doc["_id"]) async for doc in cursor]
        
        return {"park_ids": park_ids}
            
    except Exception as e:
        logging.error(f"Failed to get park IDs: {e}")
        raise HTTPException(status_code=500, detail="Failed to get park IDs")
    
@router.get("/health")
async def health():
    return {"status": "ok"}
