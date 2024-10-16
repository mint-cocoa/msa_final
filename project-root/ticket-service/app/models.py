from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from datetime import datetime

class Ticket:
    def __init__(self, db):
        self.collection = db["tickets"]

    async def create_ticket(self, ticket_data: dict):
        ticket_data["created_at"] = datetime.utcnow()
        ticket_data["updated_at"] = datetime.utcnow()
        result = await self.collection.insert_one(ticket_data)
        return str(result.inserted_id)

    async def get_ticket(self, ticket_id: str):
        ticket = await self.collection.find_one({"_id": ObjectId(ticket_id)})
        return ticket

    async def update_ticket(self, ticket_id: str, ticket_data: dict):
        ticket_data["updated_at"] = datetime.utcnow()
        result = await self.collection.update_one(
            {"_id": ObjectId(ticket_id)},
            {"$set": ticket_data}
        )
        return result.modified_count

    async def delete_ticket(self, ticket_id: str):
        result = await self.collection.delete_one({"_id": ObjectId(ticket_id)})
        return result.deleted_count

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
