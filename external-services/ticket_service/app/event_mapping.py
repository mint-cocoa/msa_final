import logging
from .event_handlers import EventHandler
from typing import Dict, Any

class EventMapper:
    def __init__(self, event_handler: EventHandler):
        self.event_handler = event_handler
        self.response_handlers = {
            # 티켓 검증 응답 핸들러
            "ticket.response.validate": self.event_handler.handle_validate_response,
            
            # 티켓 구매 응답 핸들러 (필요한 경우 추가)
            "ticket.response.purchase": self.event_handler.handle_purchase_response,
            
            # 티켓 취소 응답 핸들러 (필요한 경우 추가)
            "ticket.response.cancel": self.event_handler.handle_cancel_response,
            
            # 티켓 조회 응답 핸들러 (필요한 경우 추가)
            "ticket.response.get": self.event_handler.handle_get_response,
        }

    async def handle_ticket_response(self, routing_key: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        티켓 관련 응답을 처리합니다.
        
        Args:
            routing_key (str): 메시지의 라우팅 키
            data (Dict[str, Any]): 응답 데이터
            
        Returns:
            Dict[str, Any]: 처리된 응답 결과
        """
        try:
            handler = self.response_handlers.get(routing_key)
            
            if handler:
                result = await handler(data)
                return result
            else:
                logging.warning(f"No handler found for routing key: {routing_key}")
                return {
                    "valid": False,
                    "message": f"Unknown response type: {routing_key}"
                }
        except Exception as e:
            logging.error(f"Error handling ticket response: {e}")
            return {
                "valid": False,
                "message": f"Error processing response: {str(e)}"
            }