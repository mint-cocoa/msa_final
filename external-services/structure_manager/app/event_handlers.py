from datetime import datetime
import logging
from typing import Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from .models import PyObjectId
from .database import get_db

class EventHandler:
    def __init__(self, structure_db: AsyncIOMotorDatabase):
        self.structure_db = structure_db
        self.dbs = {}

    async def initialize_dbs(self):
        try:
            self.dbs = {
                'structure': self.structure_db,
                'park': await get_db('park'),
                'facility': await get_db('facility'),
                'ticket': await get_db('ticket')
            }
            logging.info("Successfully initialized all database connections")
        except Exception as e:
            logging.error(f"Failed to initialize databases: {e}")
            raise

    async def handle_park_create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            park_data = data.get("data", {})
            
            # parks DB에 저장
            result = await self.dbs['park'].parks.insert_one(park_data)
            park_id = result.inserted_id
            
            # structure DB의 nodes 컬렉션에 저장
            node_data = {
                "type": "park",
                "reference_id": ObjectId(park_id),
                "name": park_data.get("name"),
                "facilities": [],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            await self.dbs['structure'].nodes.insert_one(node_data)
            
            return {"status": "success", "_id": str(park_id)}
        except Exception as e:
            logging.error(f"Error creating park: {e}")
            raise

    async def handle_park_update(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            park_id = data.get("reference_id")
            park_data = data.get("data", {})
            
            # parks DB 업데이트
            result = await self.dbs['park'].parks.update_one(
                {"_id": ObjectId(park_id)},
                {"$set": park_data}
            )
            
            # structure DB의 nodes 컬렉션 업데이트
            await self.dbs['structure'].nodes.update_one(
                {"reference_id": ObjectId(park_id)},
                {"$set": {
                    "name": park_data.get("name"),
                    "updated_at": datetime.utcnow()
                }}
            )
            
            return {"status": "success", "modified_count": result.modified_count}
        except Exception as e:
            logging.error(f"Error updating park: {e}")
            raise

    async def handle_facility_create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            facility_data = data.get("data", {})
            park_id = data.get("park_id")
            
            if not park_id:
                raise Exception("Facility must have a parent park")
            
            # structure DB에서 공원 노드 확인
            park_node = await self.dbs['structure'].nodes.find_one({
                "type": "park",
                "reference_id": ObjectId(park_id)
            })
            if not park_node:
                raise Exception("Park not found")
            
            # facility DB에 저장
            result = await self.dbs['facility'].facilities.insert_one(facility_data)
            facility_id = result.inserted_id
            
            # structure DB의 nodes 컬렉션 업데이트
            await self.dbs['structure'].nodes.update_one(
                {"reference_id": ObjectId(park_id)},
                {"$push": {"facilities": facility_id}}
            )
            
            return {"status": "success", "_id": str(facility_id)}
        except Exception as e:
            logging.error(f"Error creating facility: {e}")
            raise

    async def handle_ticket_validation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            park_id = data.get("data", {}).get("park_id")
            facility_ids = data.get("data", {}).get("facility_ids")
            
            # structure DB에서 공원 노드 조회
            park_node = await self.dbs['structure'].nodes.find_one({
                "type": "park",
                "reference_id": ObjectId(park_id)
            })
            
            if not park_node:
                return {
                    "valid": False,
                    "message": "Park not found",
                    "data": data.get("data")
                }

            park_facilities = set(str(facility_id) for facility_id in park_node.get("facilities", []))
            
            for facility_id in facility_ids:
                if str(facility_id) not in park_facilities:
                    return {
                        "valid": False,
                        "message": f"Invalid facility: {facility_id}",
                        "data": data.get("data")
                    }

            return {
                "valid": True,
                "message": "Ticket validation successful",
                "data": data.get("data")
            }

        except Exception as e:
            logging.error(f"Error in ticket validation: {str(e)}")
            return {
                "valid": False,
                "message": f"Error in ticket validation: {str(e)}",
                "data": data.get("data")
            }
