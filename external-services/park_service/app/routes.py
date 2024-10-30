# park_service/app/routes.py
from fastapi import APIRouter, HTTPException, Depends, Request
from .models import ParkCreate, ParkUpdate
from .database import get_db
from .crud import create_park, update_park, delete_park, get_park
import httpx

router = APIRouter()

@router.post("/parks/create")
async def create_park_endpoint(park: ParkCreate, request: Request):
    db = await get_db()
    park_id = await create_park(db, park)
    
    # RabbitMQ를 통해 이벤트 발행
    await request.app.state.rabbitmq_publisher.publish_park_event(
        action="create",
        park_id=str(park_id),
        name=park.name
    )
    
    return {"id": str(park_id)}

@router.post("/parks/{park_id}/update")
async def update_park_endpoint(park_id: str, park: ParkUpdate, request: Request):
    # Structure Manager에 검증 요청
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{STRUCTURE_MANAGER_URL}/api/validate/park-update/{park_id}"
        )
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to validate update")
        
        validation = response.json()
        if not validation["can_update"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot update park. Has {validation['facilities_count']} facilities and {validation['ticket_types_count']} ticket types."
            )
    
    db = await get_db()
    success = await update_park(db, park_id, park)
    
    if success:
        await request.app.state.rabbitmq_publisher.publish_park_event(
            action="update",
            park_id=park_id,
            name=park.name
        )
        return {"message": "Park updated successfully"}
    raise HTTPException(status_code=404, detail="Park not found")

@router.post("/parks/{park_id}/delete")
async def delete_park_endpoint(park_id: str, request: Request):
    # Structure Manager에 검증 요청
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{STRUCTURE_MANAGER_URL}/api/validate/park-delete/{park_id}"
        )
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to validate deletion")
        
        validation = response.json()
        if not validation["can_delete"]:
            raise HTTPException(
                status_code=400, 
                detail="Cannot delete park with active facilities or tickets"
            )
    
    db = await get_db()
    success = await delete_park(db, park_id)
    
    if success:
        await request.app.state.rabbitmq_publisher.publish_park_event(
            action="delete",
            park_id=park_id
        )
        return {"message": "Park deleted successfully"}
    raise HTTPException(status_code=404, detail="Park not found")



