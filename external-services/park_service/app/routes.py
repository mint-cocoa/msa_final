# park_service/app/routes.py
from fastapi import APIRouter, HTTPException, Depends, Request
from .models import ParkCreate, ParkRead    
from .database import get_db
from bson import ObjectId
from typing import List
from common.publisher import publish_structure_update
from common.rabbitmq import RabbitMQConnection


router = APIRouter()

@router.post("/", response_model=ParkRead)
async def create_park(park: ParkCreate, db=Depends(get_db)):
    existing_park = await db.parks.find_one({"name": park.name})
    if existing_park:
        raise HTTPException(status_code=400, detail="Park already exists")
    park_data = park.model_dump(by_alias=True, exclude={"id"})
    new_park = await db.parks.insert_one(park_data)
    created_park = await db.parks.find_one({"_id": new_park.inserted_id})
    
    # 구조 업데이트 메시지 발행
    channel = await RabbitMQConnection.get_channel()
    await publish_structure_update(
        channel,
        {
            "action": "create",
            "node_type": "park",
            "reference_id": str(new_park.inserted_id),
            "name": park.name
        }
    )
    
    return created_park

@router.put("/{park_id}", response_model=ParkRead)
async def update_park(park_id: str, park: ParkCreate, request: Request, db=Depends(get_db)):
    try:
        park_object_id = ObjectId(park_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid park ID")
        
    update_result = await db.parks.update_one(
        {"_id": park_object_id},
        {"$set": park.dict(exclude_unset=True)}
    )
    
    if update_result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Park not found")
        
    # 구조 업데이트 메시지 발행
    await publish_structure_update(
        request.app.state.rabbitmq_channel,
        {
            "action": "update",
            "node_type": "park",
            "reference_id": park_id,
            "name": park.name
        }
    )
    
    updated_park = await db.parks.find_one({"_id": park_object_id})
    return updated_park

@router.get("/", response_model=List[ParkRead])
async def get_all_parks(db=Depends(get_db)):
    parks = await db.parks.find().to_list(1000)
    return parks

@router.get("/{park_id}", response_model=ParkRead)
async def get_park(park_id: str, db=Depends(get_db)):
    try:
        park_object_id = ObjectId(park_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid Park ID")
    
    park = await db.parks.find_one({"_id": park_object_id})
    if not park:
        raise HTTPException(status_code=404, detail="Park not found")
    return park



