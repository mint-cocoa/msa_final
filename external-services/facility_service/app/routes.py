from fastapi import APIRouter, HTTPException, Depends, Request
from .models import FacilityCreate, FacilityUpdate
from .database import get_db
from .crud import create_facility, update_facility, delete_facility, get_facility
import httpx

router = APIRouter()

@router.post("/facilities/create")
async def create_facility_endpoint(facility: FacilityCreate, request: Request):
    db = await get_db()
    facility_id = await create_facility(db, facility)
    
    await request.app.state.rabbitmq_publisher.publish_facility_event(
        action="create",
        facility_id=str(facility_id),
        name=facility.name,
        parent_id=str(facility.park_id)
    )
    
    return {"id": str(facility_id)}

@router.post("/facilities/{facility_id}/update")
async def update_facility_endpoint(facility_id: str, facility: FacilityUpdate, request: Request):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{STRUCTURE_MANAGER_URL}/api/validate/facility-update/{facility_id}"
        )
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to validate update")
        
        validation = response.json()
        if not validation["can_update"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot update facility. Has {validation['active_reservations_count']} active reservations."
            )
    
    db = await get_db()
    success = await update_facility(db, facility_id, facility)
    
    if success:
        await request.app.state.rabbitmq_publisher.publish_facility_event(
            action="update",
            facility_id=facility_id,
            name=facility.name,
            parent_id=str(facility.park_id)
        )
        return {"message": "Facility updated successfully"}
    raise HTTPException(status_code=404, detail="Facility not found")

@router.post("/facilities/{facility_id}/delete")
async def delete_facility_endpoint(facility_id: str, request: Request):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{STRUCTURE_MANAGER_URL}/api/validate/facility-delete/{facility_id}"
        )
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to validate deletion")
        
        validation = response.json()
        if not validation["can_delete"]:
            raise HTTPException(
                status_code=400, 
                detail="Cannot delete facility with active reservations"
            )
    
    db = await get_db()
    success = await delete_facility(db, facility_id)
    
    if success:
        await request.app.state.rabbitmq_publisher.publish_facility_event(
            action="delete",
            facility_id=facility_id
        )
        return {"message": "Facility deleted successfully"}
    raise HTTPException(status_code=404, detail="Facility not found")

