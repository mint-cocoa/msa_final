import logging
from .event_handlers import EventHandler
from typing import Dict, Any

class EventMapper:
    def __init__(self, event_handler: EventHandler):
        self.event_handler = event_handler
        self.response_handlers = {
            "park.response.create": self.event_handler.handle_create_response,
            "park.response.update": self.event_handler.handle_update_response,
            "park.response.delete": self.event_handler.handle_delete_response
        }
        
    async def handle_response(self, routing_key: str, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            handler = self.response_handlers.get(routing_key)
            if handler:
                return await handler(data)
            else:
                logging.warning(f"No handler found for routing key: {routing_key}")
                return {"status": "error", "message": f"Unknown response type: {routing_key}"}
        except Exception as e:
            logging.error(f"Error handling response: {e}")
            raise