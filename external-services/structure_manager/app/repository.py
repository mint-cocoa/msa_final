from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime
import logging
from typing import List, Optional, Dict, Any

class StructureRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.structure_nodes

    async def insert_node(self, node_data: Dict[str, Any]) -> bool:
        try:
            result = await self.collection.insert_one(node_data)
            return bool(result.inserted_id)
        except Exception as e:
            logging.error(f"Repository error - insert_node: {e}")
            raise

    async def update_node(self, query: Dict[str, Any], update_data: Dict[str, Any]) -> bool:
        try:
            result = await self.collection.update_one(query, {"$set": update_data})
            return result.modified_count > 0
        except Exception as e:
            logging.error(f"Repository error - update_node: {e}")
            raise

    async def delete_node(self, query: Dict[str, Any]) -> int:
        try:
            result = await self.collection.delete_one(query)
            return result.deleted_count
        except Exception as e:
            logging.error(f"Repository error - delete_node: {e}")
            raise

    async def delete_many_nodes(self, query: Dict[str, Any]) -> int:
        try:
            result = await self.collection.delete_many(query)
            return result.deleted_count
        except Exception as e:
            logging.error(f"Repository error - delete_many_nodes: {e}")
            raise

    async def find_node(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            return await self.collection.find_one(query)
        except Exception as e:
            logging.error(f"Repository error - find_node: {e}")
            raise

    async def update_parent_children(self, parent_id: str, child_id: str, action: str) -> bool:
        try:
            if action == "add":
                update = {"$push": {"children": ObjectId(child_id)}}
            elif action == "remove":
                update = {"$pull": {"children": ObjectId(child_id)}}
            else:
                raise ValueError(f"Invalid action: {action}")

            result = await self.collection.update_one(
                {"reference_id": ObjectId(parent_id)},
                update
            )
            return result.modified_count > 0
        except Exception as e:
            logging.error(f"Repository error - update_parent_children: {e}")
            raise

    async def get_node_with_children(self, reference_id: str) -> Optional[Dict[str, Any]]:
        try:
            pipeline = [
                {"$match": {"reference_id": ObjectId(reference_id)}},
                {
                    "$lookup": {
                        "from": "structure_nodes",
                        "localField": "children",
                        "foreignField": "_id",
                        "as": "children_data"
                    }
                }
            ]
            result = await self.collection.aggregate(pipeline).to_list(None)
            return result[0] if result else None
        except Exception as e:
            logging.error(f"Repository error - get_node_with_children: {e}")
            raise 