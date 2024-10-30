from datetime import datetime
from .models import ReservationCreate, ReservationResponse
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

async def create_reservation(db: AsyncIOMotorDatabase, reservation: ReservationCreate):
    reservation_data = reservation.dict()
    reservation_data["created_at"] = datetime.utcnow()
    reservation_data["updated_at"] = datetime.utcnow()
    reservation_data["status"] = "pending"
    
    result = await db.reservations.insert_one(reservation_data)
    return str(result.inserted_id)

async def get_reservation(db: AsyncIOMotorDatabase, reservation_id: str):
    reservation = await db.reservations.find_one({"_id": ObjectId(reservation_id)})
    return reservation

async def update_reservation_status(db: AsyncIOMotorDatabase, reservation_id: str, status: str):
    result = await db.reservations.update_one(
        {"_id": ObjectId(reservation_id)},
        {
            "$set": {
                "status": status,
                "updated_at": datetime.utcnow()
            }
        }
    )
    return result.modified_count > 0

async def get_active_reservations(db: AsyncIOMotorDatabase, facility_id: str):
    cursor = db.reservations.find({
        "facility_id": ObjectId(facility_id),
        "status": {"$in": ["pending", "confirmed"]},
        "reservation_time": {"$gte": datetime.utcnow()}
    })
    return await cursor.to_list(None)

async def cancel_reservation(db: AsyncIOMotorDatabase, reservation_id: str):
    result = await db.reservations.update_one(
        {"_id": ObjectId(reservation_id)},
        {
            "$set": {
                "status": "cancelled",
                "updated_at": datetime.utcnow()
            }
        }
    )
    return result.modified_count > 0 