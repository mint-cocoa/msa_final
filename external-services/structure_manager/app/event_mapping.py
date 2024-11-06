from typing import Dict, Callable, Any
from .event_handlers import EventHandler

class EventMapper:
    def __init__(self, event_handler: EventHandler):
        self.handler = event_handler
        self.update_mappings = {
            "park.updates.update": self.handler.handle_park_update,
            "park.updates.delete": self.handler.handle_park_delete,
            "facility.updates.create": self.handler.handle_facility_create,
            "facility.updates.update": self.handler.handle_facility_update,
            "facility.updates.delete": self.handler.handle_facility_delete,
        }
        self.rpc_mappings = {
            "park.create": self.handler.handle_park_create,
        }

    async def route_event(self, routing_key: str, data: dict) -> None:
        handler = self.update_mappings.get(routing_key)
        if handler:
            await handler(data)

    async def handle_rpc(self, routing_key: str, data: dict) -> dict:
        handler = self.rpc_mappings.get(routing_key)
        if handler:
            return await handler(data)
        return {"error": f"No handler found for routing key: {routing_key}"}