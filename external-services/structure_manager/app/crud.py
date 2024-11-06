from datetime import datetime
from bson import ObjectId
import logging
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Optional, Dict
from .repository import StructureRepository

class StructureNodeCRUD:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.repository = StructureRepository(db)

    async def create_node(self, 
                         node_type: str,
                         reference_id: str,
                         name: str,
                         parent_id: Optional[str] = None) -> bool:
        try:
            node_data = {
                "node_type": node_type,
                "reference_id": ObjectId(reference_id),
                "name": name,
                "children": [],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }

            if parent_id:
                # 부모 노드 존재 확인
                parent = await self.repository.find_node({"reference_id": ObjectId(parent_id)})
                if not parent:
                    logging.error(f"Parent node not found: {parent_id}")
                    return False

                node_data["parent_id"] = ObjectId(parent_id)
                # 노드 생성
                success = await self.repository.insert_node(node_data)
                if success:
                    # 부모 노드의 children 업데이트
                    await self.repository.update_parent_children(parent_id, reference_id, "add")
                return success
            else:
                node_data["parent_id"] = None
                return await self.repository.insert_node(node_data)

        except Exception as e:
            logging.error(f"Error creating structure node: {e}")
            raise

    async def update_node(self,
                         reference_id: str,
                         name: str,
                         parent_id: Optional[str] = None) -> bool:
        try:
            current_node = await self.repository.find_node({"reference_id": ObjectId(reference_id)})
            if not current_node:
                return False

            update_data = {
                "name": name,
                "updated_at": datetime.utcnow()
            }

            if parent_id and str(current_node.get("parent_id")) != parent_id:
                # 이전 부모에서 제거
                if current_node.get("parent_id"):
                    await self.repository.update_parent_children(
                        str(current_node["parent_id"]), 
                        reference_id, 
                        "remove"
                    )
                
                # 새 부모에 추가
                await self.repository.update_parent_children(parent_id, reference_id, "add")
                update_data["parent_id"] = ObjectId(parent_id)

            return await self.repository.update_node(
                {"reference_id": ObjectId(reference_id)},
                update_data
            )

        except Exception as e:
            logging.error(f"Error updating structure node: {e}")
            raise

    async def delete_node(self, reference_id: str, with_descendants: bool = False) -> int:
        try:
            node = await self.repository.find_node({"reference_id": ObjectId(reference_id)})
            if not node:
                return 0

            total_deleted = 0

            if with_descendants:
                # 모든 하위 노드 삭제
                total_deleted = await self.repository.delete_many_nodes({
                    "$or": [
                        {"reference_id": ObjectId(reference_id)},
                        {"ancestors": ObjectId(reference_id)}
                    ]
                })
            else:
                # 현재 노드만 삭제
                total_deleted = await self.repository.delete_node(
                    {"reference_id": ObjectId(reference_id)}
                )

            # 부모 노드에서 현재 노드 제거
            if node.get("parent_id"):
                await self.repository.update_parent_children(
                    str(node["parent_id"]),
                    reference_id,
                    "remove"
                )

            return total_deleted

        except Exception as e:
            logging.error(f"Error deleting structure node: {e}")
            raise

    async def get_node(self, reference_id: str):
        try:
            return await self.repository.find_node({"reference_id": ObjectId(reference_id)})
        except Exception as e:
            logging.error(f"Error getting structure node: {e}")
            raise

    async def get_children(self, reference_id: str):
        try:
            node = await self.get_node(reference_id)
            if not node:
                return []
            
            children = []
            for child_id in node.get("children", []):
                child = await self.repository.find_node({"reference_id": child_id})
                if child:
                    children.append(child)
            return children
        except Exception as e:
            logging.error(f"Error getting node children: {e}")
            raise

    async def validate_park_delete(self, park_id: str) -> Dict[str, any]:
        """공원 삭제 가능 여부를 검증"""
        try:
            node = await self.repository.find_node({"reference_id": ObjectId(park_id)})
            if not node:
                return {"can_delete": False, "reason": "Park not found"}
            
            children = node.get("children", [])
            return {
                "can_delete": len(children) == 0,
                "facilities_count": len(children)
            }
        except Exception as e:
            logging.error(f"Error validating park delete: {e}")
            raise

    async def validate_park_update(self, park_id: str) -> Dict[str, any]:
        """공원 업데이트 가능 여부를 검증"""
        try:
            node = await self.repository.find_node({"reference_id": ObjectId(park_id)})
            if not node:
                return {"can_update": False, "reason": "Park not found"}
            
            children = node.get("children", [])
            return {
                "can_update": True,  # 공원은 항상 업데이트 가능
                "facilities_count": len(children)
            }
        except Exception as e:
            logging.error(f"Error validating park update: {e}")
            raise