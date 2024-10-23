from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from datetime import datetime

class Ticket:
    def __init__(self, db):
        self.collection = db["tickets"]

    # ... (기존 메서드 유지)

    async def get_ticket_by_token(self, token: str):
        ticket = await self.collection.find_one({"token": token})
        return ticket

    async def update_ticket_status(self, ticket_id: str, status: str):
        update_data = {"status": status, "updated_at": datetime.utcnow()}
        result = await self.collection.update_one(
            {"_id": ObjectId(ticket_id)},
            {"$set": update_data}
        )
        if result.modified_count == 0:
            return None
        return await self.get_ticket(ticket_id)
