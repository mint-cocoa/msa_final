from fastapi import APIRouter, HTTPException, Request
from .models import FacilityModel
import logging

router = APIRouter()

@router.post("/parks/{park_id}/facilities")
async def create_facility_endpoint(park_id: str, facility: FacilityModel, request: Request):
    try:
        await request.app.state.publisher.publish_structure_update({
            "action": "create",
            "node_type": "facility",
            "name": facility.name,
            "parent_id": park_id,
            "data": facility.dict()
        })
        return {"message": "Facility creation request sent successfully"}
    except Exception as e:
        logging.error(f"Failed to send facility creation event: {e}")
        raise HTTPException(status_code=500, detail="Failed to create facility")

@router.post("/parks/{park_id}/facilities/{facility_id}")
async def update_facility_endpoint(park_id: str, facility_id: str, facility: FacilityModel, request: Request):
    try:
        await request.app.state.publisher.publish_structure_update({
            "action": "update",
            "node_type": "facility",
            "reference_id": facility_id,
            "name": facility.name,
            "parent_id": park_id,
            "data": facility.dict()
        })
        return {"message": "Facility update request sent successfully"}
    except Exception as e:
        logging.error(f"Failed to send facility update event: {e}")
        raise HTTPException(status_code=500, detail="Failed to update facility")

@router.delete("/parks/{park_id}/facilities/{facility_id}")
async def delete_facility_endpoint(park_id: str, facility_id: str, request: Request):
    try:
        await request.app.state.publisher.publish_structure_update({
            "action": "delete",
            "node_type": "facility",
            "reference_id": facility_id,
            "parent_id": park_id
        })
        return {"message": "Facility deletion request sent successfully"}
    except Exception as e:
        logging.error(f"Failed to send facility deletion event: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete facility")

@router.get("/parks/{park_id}/facilities/{facility_id}")
async def get_facility_endpoint(park_id: str, facility_id: str, request: Request):
    try:
        await request.app.state.publisher.publish_structure_update({
            "action": "get",
            "node_type": "facility",
            "reference_id": facility_id,
            "parent_id": park_id
        })
        return {"message": "Facility retrieval request sent successfully"}
    except Exception as e:
        logging.error(f"Failed to send facility retrieval event: {e}")
        raise HTTPException(status_code=500, detail="Failed to get facility")

@router.get("/parks/{park_id}/facilities")
async def get_park_facilities_endpoint(park_id: str, request: Request):
    try:
        await request.app.state.publisher.publish_structure_update({
            "action": "get_children",
            "node_type": "park",
            "reference_id": park_id
        })
        return {"message": "Park facilities retrieval request sent successfully"}
    except Exception as e:
        logging.error(f"Failed to send park facilities retrieval event: {e}")
        raise HTTPException(status_code=500, detail="Failed to get park facilities")
