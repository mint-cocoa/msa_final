import logging
from typing import Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import asyncio

logger = logging.getLogger(__name__)

class EventHandler:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.tickets = {}  # 메모리에 임시 저장
        self.latest_response = None  # 가장 최근 응답 저장
        logger.info("EventHandler initialized")

    async def handle_create_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            self.latest_response = data
            logger.info(f"Received create response: {data}")
            ticket_id = data.get("_id")
            if ticket_id:
                self.tickets[ticket_id] = data
            return {"status": "success", "data": data}
        except Exception as e:
            logger.error(f"Error handling create response: {e}", exc_info=True)
            raise

    async def handle_validate_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            self.latest_response = data
            logger.info(f"Received validate response: {data}")
            
            valid = data.get("valid", False)
            message = data.get("message", "")
            ticket_data = data.get("data", {})

            if not valid:
                logger.warning(f"Ticket validation failed: {message}")
            else:
                logger.info("Ticket validation successful")

            return {
                "valid": valid,
                "message": message,
                "data": ticket_data
            }
        except Exception as e:
            logger.error(f"Error handling validate response: {e}", exc_info=True)
            raise

    async def handle_purchase_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            self.latest_response = data
            logger.info(f"Received purchase response: {data}")
            
            success = data.get("success", False)
            message = data.get("message", "")
            ticket_data = data.get("data", {})

            if success:
                ticket_data["created_at"] = datetime.utcnow()
                await self.db.tickets.insert_one(ticket_data)
                logger.info(f"Ticket saved to database: {ticket_data}")

            return {
                "status": "success",
                "message": message,
                "data": ticket_data
            }
        except Exception as e:
            logger.error(f"Error handling purchase response: {e}", exc_info=True)
            raise

    async def handle_cancel_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            self.latest_response = data
            logger.info(f"Received cancel response: {data}")
            
            ticket_id = data.get("ticket_id")
            if ticket_id and ticket_id in self.tickets:
                del self.tickets[ticket_id]
                await self.db.tickets.update_one(
                    {"_id": ObjectId(ticket_id)},
                    {"$set": {
                        "status": "cancelled",
                        "cancelled_at": datetime.utcnow()
                    }}
                )
            return {"status": "success", "data": data}
        except Exception as e:
            logger.error(f"Error handling cancel response: {e}", exc_info=True)
            raise

    async def handle_get_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            self.latest_response = data
            logger.info(f"Received get response: {data}")
            return {"status": "success", "data": data}
        except Exception as e:
            logger.error(f"Error handling get response: {e}", exc_info=True)
            raise

