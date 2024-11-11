import logging
from .event_handlers import EventHandler
from typing import Dict, Any

class EventMapper:
    def __init__(self, event_handler: EventHandler):
        self.event_handler = event_handler
        self.request_handlers = {
            # Park 요청 핸들러
            "park.request.create": self.event_handler.handle_park_create,
            
            # Facility 요청 핸들러
            "facility.request.create": self.event_handler.handle_facility_create,
            
            # Ticket 요청 핸들러
            "ticket.request.validate": self.event_handler.handle_ticket_validation
        }

    async def handle_request(self, routing_key: str, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            handler = self.request_handlers.get(routing_key)
            if handler:
                return await handler(data)
            else:
                logging.warning(f"No handler found for routing key: {routing_key}")
                return {"status": "error", "message": f"Unknown request type: {routing_key}"}
        except Exception as e:
            logging.error(f"Error handling request: {e}")
            raise 