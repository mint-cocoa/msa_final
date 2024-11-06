# park_service/app/routes.py
from fastapi import APIRouter, HTTPException, Request
from .models import ParkModel
import logging

router = APIRouter()

@router.post("/parks/create")
async def create_park_endpoint(park: ParkModel, request: Request):
    try:
        # RPC 호출로 park 생성 요청
        response = await request.app.state.publisher.create_park({
            "action": "create",
            "node_type": "park",
            "name": park.name,
            "data": park.dict()
        })
        
        if "error" in response:
            raise HTTPException(status_code=400, detail=response["error"])
            
        return {
            "message": "Park created successfully",
            "park_id": response["park_id"]
        }
    except Exception as e:
        logging.error(f"Failed to create park: {e}")
        raise HTTPException(status_code=500, detail="Failed to create park")

@router.post("/parks/{park_id}/update")
async def update_park_endpoint(park_id: str, park: ParkModel, request: Request):
    try:
        # 구조 업데이트 이벤트 발행
        await request.app.state.publisher.publish_structure_update({
            "action": "update",
            "node_type": "park",
            "reference_id": park_id,
            "name": park.name,
            "data": park.dict()  # 업데이트할 park 데이터를 포함
        })
        return {"message": "Park update request sent successfully"}
    except Exception as e:
        logging.error(f"Failed to send park update event: {e}")
        raise HTTPException(status_code=500, detail="Failed to update park")

@router.post("/parks/{park_id}/delete")
async def delete_park_endpoint(park_id: str, request: Request):
    try:
        # 구조 업데이트 이벤트 발행
        await request.app.state.publisher.publish_structure_update({
            "action": "delete",
            "node_type": "park",
            "reference_id": park_id
        })
        return {"message": "Park deletion request sent successfully"}
    except Exception as e:
        logging.error(f"Failed to send park deletion event: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete park")

@router.get("/parks/{park_id}")
async def get_park_endpoint(park_id: str, request: Request):
    try:
        # 구조 조회 이벤트 발행
        await request.app.state.publisher.publish_structure_update({
            "action": "get",
            "node_type": "park",
            "reference_id": park_id
        })
        return {"message": "Park retrieval request sent successfully"}
    except Exception as e:
        logging.error(f"Failed to send park retrieval event: {e}")
        raise HTTPException(status_code=500, detail="Failed to get park")



