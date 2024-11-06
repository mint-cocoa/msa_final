from datetime import datetime
import logging
from .crud import StructureNodeCRUD
from bson import ObjectId

class EventHandler:
    def __init__(self, db):
        self.crud = StructureNodeCRUD(db)

    async def handle_park_create(self, data: dict) -> dict:
        try:
            # 노드 생성
            node_data = {
                "node_type": "park",
                "name": data["name"],
                "data": data["data"]
            }
            
            # 노드 생성 및 ID 반환
            node_id = await self.crud.create_node(**node_data)
            
            if node_id:
                logging.info(f"Created park structure node: {data['name']}")
                return {
                    "park_id": str(node_id),
                    "status": "success"
                }
            else:
                return {
                    "error": "Failed to create park",
                    "status": "error"
                }
        except Exception as e:
            logging.error(f"Error creating park structure: {e}")
            return {
                "error": str(e),
                "status": "error"
            }

    async def handle_park_update(self, data: dict):
        try:
            success = await self.crud.update_node(
                reference_id=data["reference_id"],
                name=data["name"]
            )
            if success:
                logging.info(f"Updated park structure node: {data['name']}")
        except Exception as e:
            logging.error(f"Error updating park structure: {e}")
            raise

    async def handle_park_delete(self, data: dict):
        try:
            deleted_count = await self.crud.delete_node(
                reference_id=data["reference_id"],
                with_descendants=True
            )
            logging.info(f"Deleted park and related structures: {deleted_count} nodes")
        except Exception as e:
            logging.error(f"Error deleting park structure: {e}")
            raise

    async def handle_facility_create(self, data: dict):
        try:
            success = await self.crud.create_node(
                node_type="facility",
                reference_id=data["reference_id"],
                name=data["name"],
                parent_id=data["parent_id"]
            )
            if success:
                logging.info(f"Created facility structure node: {data['name']}")
        except Exception as e:
            logging.error(f"Error creating facility structure: {e}")
            raise

    async def handle_facility_update(self, data: dict):
        try:
            success = await self.crud.update_node(
                reference_id=data["reference_id"],
                name=data["name"],
                parent_id=data["parent_id"]
            )
            if success:
                logging.info(f"Updated facility structure node: {data['name']}")
        except Exception as e:
            logging.error(f"Error updating facility structure: {e}")
            raise

    async def handle_facility_delete(self, data: dict):
        try:
            deleted_count = await self.crud.delete_node(
                reference_id=data["reference_id"]
            )
            if deleted_count:
                logging.info(f"Deleted facility structure node: {data['reference_id']}")
        except Exception as e:
            logging.error(f"Error deleting facility structure: {e}")
            raise