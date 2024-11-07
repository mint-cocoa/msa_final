import logging
from .event_handlers import EventHandler
from typing import Dict, Any

class EventMapper:
    def __init__(self, event_handler: EventHandler):
        self.event_handler = event_handler
        self.response_handlers = {
            "facility.response.create": self.event_handler.handle_create_response,
            "facility.response.update": self.event_handler.handle_update_response,
            "facility.response.delete": self.event_handler.handle_delete_response,
            "facility.response.get": self.event_handler.handle_get_response,
            "facility.response.get_all": self.event_handler.handle_get_response,
        }

    async def handle_response(self, routing_key: str, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            handler = self.response_handlers.get(routing_key)
            if handler:
                return await handler(data)
            else:
                logging.warning(f"No handler found for routing key: {routing_key}")
                return {"status": "error", "message": "Unknown response type"}
        except Exception as e:
            logging.error(f"Error handling response: {e}")
            raise 