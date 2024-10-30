from fastapi import FastAPI, Request
import aio_pika
import json
from .models import FacilityCreate
from .database import db

app = FastAPI(
    title="Facility Service",
    description="Service for managing facilities",
    version="1.0.0"
)

@app.post("/facilities")
async def create_facility(facility: FacilityCreate, request: Request):
    # 시설 생성 로직
    new_facility = await db.facilities.insert_one(facility.dict())
    
    # 변경 사항을 ParkAccessManager에 알림
    message = aio_pika.Message(
        body=json.dumps({
            "facility_id": str(new_facility.inserted_id),
            "parent_id": facility.parent_id
        }).encode()
    )
    await request.app.state.rabbitmq_channel.default_exchange.publish(
        message, routing_key="facility_updates"
    )
    
    return {"id": str(new_facility.inserted_id)} 