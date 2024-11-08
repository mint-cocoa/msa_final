from datetime import datetime
import logging
from typing import Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from .models import PyObjectId

class EventHandler:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    # Park 핸들러
    async def handle_park_create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            park_data = data.get("data", {})
            
            # parks 컬렉션에 저장
            result = await self.db.parks.insert_one(park_data)
            park_id = result.inserted_id
            
            # nodes 컬렉션에 구조 정보 저장
            node_data = {
                "type": "park",
                "reference_id": ObjectId(park_id),
                "name": park_data.get("name"),
                "facilities": [],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            await self.db.nodes.insert_one(node_data)
            
            return {"status": "success", "_id": str(park_id)}
        except Exception as e:
            logging.error(f"Error creating park: {e}")
            raise

    async def handle_park_update(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            park_id = data.get("reference_id")
            park_data = data.get("data", {})
            
            result = await self.db.parks.update_one(
                {"_id": ObjectId(park_id)},
                {"$set": park_data}
            )
            
            # 노드 정보 업데이트
            await self.db.nodes.update_one(
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
            
            # 공원 노드 존재 확인
            park_node = await self.db.nodes.find_one({
                "type": "park",
                "reference_id": ObjectId(park_id)
            })
            if not park_node:
                raise Exception("park not found")
            
            # facilities 컬렉션에 저장
            result = await self.db.facilities.insert_one(facility_data)
            facility_id = result.inserted_id
            
            # 공원 노드의 facilities 배열에 시설물 ID 추가
            await self.db.nodes.update_one(
                {"reference_id": ObjectId(park_id)},
                {"$push": {"facilities": facility_id}}
            )
            
            return {"status": "success", "_id": str(facility_id)}
        except Exception as e:
            logging.error(f"Error creating facility: {e}")
            raise

    async def handle_facility_delete(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            facility_id = data.get("reference_id")
            park_id = data.get("park_id")
            
            # 시설물 삭제
            result = await self.db.facilities.delete_one({"_id": ObjectId(facility_id)})
            
            # 공원 노드에서 시설물 ID 제거
            await self.db.nodes.update_one(
                {"reference_id": park_id},
                {"$pull": {"facilities": ObjectId(facility_id)}}
            )
            
            return {"status": "success", "deleted_count": result.deleted_count}
        except Exception as e:
            logging.error(f"Error deleting facility: {e}")
            raise

    async def handle_park_delete(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            park_id = data.get("reference_id")
            
            # 공원 노드 삭제
            await self.db.nodes.delete_one({"reference_id": ObjectId(park_id)})
            
            # 공원 데이터 삭제
            result = await self.db.parks.delete_one({"_id": ObjectId(park_id)})
            
            return {"status": "success", "deleted_count": result.deleted_count}
        except Exception as e:
            logging.error(f"Error deleting park: {e}")
            raise

    async def handle_park_get(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            park_id = data.get("reference_id")
            park = await self.db.parks.find_one({"_id": ObjectId(park_id)})
            
            if park:
                park["_id"] = str(park["_id"])
                return {"status": "success", "data": park}
            else:
                return {"status": "error", "message": "Park not found"}
        except Exception as e:
            logging.error(f"Error getting park: {e}")
            raise

    async def handle_park_get_all(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            parks = await self.db.parks.find().to_list(length=None)
            for park in parks:
                park["_id"] = str(park["_id"])
            return {"status": "success", "data": parks}
        except Exception as e:
            logging.error(f"Error getting all parks: {e}")
            raise

    async def handle_facility_update(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            facility_id = data.get("reference_id")
            facility_data = data.get("data", {})
            
            result = await self.db.facilities.update_one(
                {"_id": ObjectId(facility_id)},
                {"$set": facility_data}
            )
            
            return {"status": "success", "modified_count": result.modified_count}
        except Exception as e:
            logging.error(f"Error updating facility: {e}")
            raise

    async def handle_facility_get(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            facility_id = data.get("reference_id")
            facility = await self.db.facilities.find_one({"_id": ObjectId(facility_id)})
            
            if facility:
                facility["_id"] = str(facility["_id"])
                return {"status": "success", "data": facility}
            else:
                return {"status": "error", "message": "Facility not found"}
        except Exception as e:
            logging.error(f"Error getting facility: {e}")
            raise

    async def handle_facility_get_all(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            facilities = await self.db.facilities.find().to_list(length=None)
            for facility in facilities:
                facility["_id"] = str(facility["_id"])
            return {"status": "success", "data": facilities}
        except Exception as e:
            logging.error(f"Error getting all facilities: {e}")
            raise

    async def handle_facility_validation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            logging.info(f"시설 유효성 검사 시작: {data}")
            park_id = data.get("data", {}).get("park_id")
            facility_ids = data.get("data", {}).get("facility_ids")
            
            logging.info(f"공원 노드 조회 시작: park_id={park_id}")
            # 공원 노드 조회
            park_node = await self.db.nodes.find_one({
                "type": "park",
                "reference_id": ObjectId(park_id)
            })
            
            if not park_node:
                logging.warning(f"park not found: park_id={park_id}")
                return {
                    "valid": False,
                    "message": "park not found",
                    "data": data.get("data")
                }

            logging.info(f"facility validation start: facility_ids={facility_ids}")
            # 시설 유효성 검사 - park_node의 facilities 배열 활용
            park_facilities = set(str(facility_id) for facility_id in park_node.get("facilities", []))
            
            for facility_id in facility_ids:
                if str(facility_id) not in park_facilities:
                    logging.warning(f"invalid facility found: facility_id={facility_id}, park_id={park_id}")
                    return {
                        "valid": False,
                        "message": f"invalid facility found: {facility_id}",
                        "data": data.get("data")
                    }

            logging.info("시설 유효성 검사 완료: 모든 검증 통과")
            return {
                "valid": True,
                "message": "시설 유효성 검사 완료",
                "data": {
                    **data.get("data", {}),
                }
            }

        except Exception as e:
            logging.error(f"시설 유효성 검사 중 오류 발생: {str(e)}", exc_info=True)
            return {
                "valid": False,
                "message": f"시설 유효성 검사 중 오류가 발생했습니다: {str(e)}",
                "data": data.get("data")
            }

    # 기타 핸들러들은 동일하게 유지...