import logging
from typing import Dict, Any

class EventHandler:
    def __init__(self):
        self.parks = {}  # 메모리에 임시 저장
        self.latest_response = None  # 가장 최근 응답 저장

    async def handle_create_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            self.latest_response = data
            logging.info(f"Received create response: {data}")
            park_id = data.get("_id")
            if park_id:
                self.parks[park_id] = data
            return {"status": "success", "data": data}
        except Exception as e:
            logging.error(f"Error handling create response: {e}")
            raise

    async def handle_update_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            self.latest_response = data
            park_id = data.get("_id")
            if park_id and park_id in self.parks:
                self.parks[park_id].update(data)
            return {"status": "success", "data": data}
        except Exception as e:
            logging.error(f"Error handling update response: {e}")
            raise

    async def handle_delete_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            self.latest_response = data
            park_id = data.get("reference_id")
            if park_id and park_id in self.parks:
                del self.parks[park_id]
            return {"status": "success", "data": data}
        except Exception as e:
            logging.error(f"Error handling delete response: {e}")
            raise

    async def handle_get_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            self.latest_response = data
            return {"status": "success", "data": data}
        except Exception as e:
            logging.error(f"Error handling get response: {e}")
            raise

    async def handle_get_all_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            self.latest_response = data
            return {"status": "success", "data": data}
        except Exception as e:
            logging.error(f"Error handling get all response: {e}")
            raise 