import logging
from .event_handlers import EventHandler
from typing import Dict, Any

class EventMapper:
    def __init__(self, event_handler: EventHandler):
        self.event_handler = event_handler
        self.response_handlers = {
            "ticket.response.validate_access": self.event_handler.handle_ticket_validation_response,
            "ticket.response.error": self.event_handler.handle_error_response
        }

    async def handle_response(self, routing_key: str, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            handler = self.response_handlers.get(routing_key)
            if handler:
                return await handler(data)
            else:
                logging.warning(f"라우팅 키에 대한 핸들러를 찾을 수 없음: {routing_key}")
                return {
                    "status": "error",
                    "message": f"알 수 없는 응답 유형: {routing_key}"
                }
        except Exception as e:
            logging.error(f"이벤트 매퍼 오류: {e}")
            raise 