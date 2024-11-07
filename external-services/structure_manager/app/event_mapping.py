import logging
from .event_handlers import EventHandler
from typing import Dict, Any

class EventMapper:
    def __init__(self, event_handler: EventHandler):
        self.event_handler = event_handler
        self.request_handlers = {
            # Park 요청 핸들러
            "park.create": self.event_handler.handle_park_create,
            "park.update": self.event_handler.handle_park_update,
            "park.delete": self.event_handler.handle_park_delete,
            "park.get": self.event_handler.handle_park_get,
            "park.get_all": self.event_handler.handle_park_get_all,
            
            # Facility 요청 핸들러
            "facility.create": self.event_handler.handle_facility_create,
            "facility.update": self.event_handler.handle_facility_update,
            "facility.delete": self.event_handler.handle_facility_delete,
            "facility.get": self.event_handler.handle_facility_get,
            "facility.get_all": self.event_handler.handle_facility_get_all,
            
            # Structure 요청 핸들러
            "structure.validate_facilities": self.event_handler.handle_facility_validation
        }

    async def handle_park_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            action = data.get("action")
            routing_key = f"park.{action}"
            handler = self.request_handlers.get(routing_key)
            
            if handler:
                result = await handler(data)
                return result
            else:
                logging.warning(f"No handler found for park action: {action}")
                return {"status": "error", "message": "Unknown park action"}
        except Exception as e:
            logging.error(f"Error handling park request: {e}")
            raise

    async def handle_facility_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            action = data.get("action")
            routing_key = f"facility.{action}"
            handler = self.request_handlers.get(routing_key)
            
            if handler:
                result = await handler(data)
                return result
            else:
                logging.warning(f"No handler found for facility action: {action}")
                return {"status": "error", "message": "Unknown facility action"}
        except Exception as e:
            logging.error(f"Error handling facility request: {e}")
            raise

    async def handle_structure_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            action = data.get("action")
            routing_key = f"structure.{action}"
            handler = self.request_handlers.get(routing_key)
            
            if handler:
                result = await handler(data)
                return result
            else:
                logging.warning(f"No handler found for structure action: {action}")
                return {"status": "error", "message": "Unknown structure action"}
        except Exception as e:
            logging.error(f"Error handling structure request: {e}")
            raise