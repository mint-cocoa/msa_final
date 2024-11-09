import logging
from typing import Dict, Any

class EventHandler:
    def __init__(self):
        self.facilities = {}  # 메모리에 임시 저장

    async def handle_create_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            facility_id = data.get("_id")
            if facility_id:
                self.facilities[facility_id] = data
            return {"status": "success", "data": data}
        except Exception as e:
            logging.error(f"Error handling create response: {e}")
            raise

    async def handle_update_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            facility_id = data.get("_id")
            if facility_id and facility_id in self.facilities:
                self.facilities[facility_id].update(data)
            return {"status": "success", "data": data}
        except Exception as e:
            logging.error(f"Error handling update response: {e}")
            raise

    async def handle_delete_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            facility_id = data.get("reference_id")
            if facility_id and facility_id in self.facilities:
                del self.facilities[facility_id]
            return {"status": "success", "data": data}
        except Exception as e:
            logging.error(f"Error handling delete response: {e}")
            raise

    async def handle_get_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return {"status": "success", "data": data}
        except Exception as e:
            logging.error(f"Error handling get response: {e}")
            raise             