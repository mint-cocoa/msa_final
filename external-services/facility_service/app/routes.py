from fastapi import APIRouter, HTTPException, Request
from .models import FacilityModel
import logging

router = APIRouter()

@router.post("/facilities/create")
async def create_facility_endpoint(facility: FacilityModel, request: Request):
    try:
        # 구조 업데이트 이벤트 발행
        await request.app.state.publisher.publish_structure_update({
            "action": "create",
            "node_type": "facility",
            "name": facility.name,
            "parent_id": str(facility.park_id),
            "data": facility.dict()  # 전체 facility 데이터를 포함
        })
        
        return {"message": "Facility creation request sent successfully"}
    except Exception as e:
        logging.error(f"Failed to send facility creation event: {e}")
        raise HTTPException(status_code=500, detail="Failed to create facility")

@router.post("/facilities/{facility_id}/update")
async def update_facility_endpoint(facility_id: str, facility: FacilityModel, request: Request):
    try:
        # 구조 업데이트 이벤트 발행
        await request.app.state.publisher.publish_structure_update({
            "action": "update",
            "node_type": "facility",
            "reference_id": facility_id,
            "name": facility.name,
            "parent_id": str(facility.park_id),
            "data": facility.dict()  # 업데이트할 facility 데이터를 포함
        })
        return {"message": "Facility update request sent successfully"}
    except Exception as e:
        logging.error(f"Failed to send facility update event: {e}")
        raise HTTPException(status_code=500, detail="Failed to update facility")

@router.post("/facilities/{facility_id}/delete")
async def delete_facility_endpoint(facility_id: str, request: Request):
    try:
        # 구조 업데이트 이벤트 발행
        await request.app.state.publisher.publish_structure_update({
            "action": "delete",
            "node_type": "facility",
            "reference_id": facility_id
        })
        return {"message": "Facility deletion request sent successfully"}
    except Exception as e:
        logging.error(f"Failed to send facility deletion event: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete facility")

@router.get("/facilities/{facility_id}")
async def get_facility_endpoint(facility_id: str, request: Request):
    try:
        # 구조 조회 이벤트 발행
        await request.app.state.publisher.publish_structure_update({
            "action": "get",
            "node_type": "facility",
            "reference_id": facility_id
        })
        return {"message": "Facility retrieval request sent successfully"}
    except Exception as e:
        logging.error(f"Failed to send facility retrieval event: {e}")
        raise HTTPException(status_code=500, detail="Failed to get facility")

@router.get("/facilities/park/{park_id}")
async def get_park_facilities(park_id: str, request: Request):
    try:
        # 구조 조회 이벤트 발행
        await request.app.state.publisher.publish_structure_update({
            "action": "get_children",
            "node_type": "park",
            "reference_id": park_id
        })
        return {"message": "Park facilities retrieval request sent successfully"}
    except Exception as e:
        logging.error(f"Failed to send park facilities retrieval event: {e}")
        raise HTTPException(status_code=500, detail="Failed to get park facilities")
