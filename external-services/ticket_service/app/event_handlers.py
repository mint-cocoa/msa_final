import logging
from typing import Dict, Any
from datetime import datetime

class EventHandler:
    def __init__(self, db):
        self.db = db
        self.latest_response = None

    async def handle_ticket_validation_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            self.latest_response = data
            validation_result = data.get("data", {})
            
            if not validation_result.get("valid", False):
                return {
                    "status": "error",
                    "message": validation_result.get("message", "시설 접근이 거부되었습니다."),
                    "data": validation_result
                }
                
            # 티켓 데이터 준비
            ticket_data = {
                "user_id": validation_result.get("user_id"),
                "park_id": validation_result.get("park_id"),
                "ticket_type_name": validation_result.get("ticket_type_name"),
                "allowed_facilities": validation_result.get("allowed_facilities", []),
                "purchase_date": datetime.utcnow(),
                "amount": validation_result.get("amount", 0),
                "available_date": datetime.utcnow().strftime("%Y-%m-%d"),
                "used": False
            }
            
            # 티켓 저장
            result = await self.db.tickets.insert_one(ticket_data)
            
            return {
                "status": "success",
                "ticket_id": str(result.inserted_id),
                "message": "티켓이 성공적으로 생성되었습니다.",
                "data": {
                    "ticket_type": validation_result.get("ticket_type_name"),
                    "allowed_facilities": validation_result.get("allowed_facilities", []),
                    "amount": validation_result.get("amount", 0)
                }
            }
        except Exception as e:
            logging.error(f"시설 접근 유효성 검사 응답 처리 중 오류: {e}")
            return {
                "status": "error",
                "message": f"티켓 생성 중 오류가 발생했습니다: {str(e)}"
            }

    async def handle_error_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """에러 응답 처리 메서드"""
        self.latest_response = data
        error_message = data.get("message", "알 수 없는 오류가 발생했습니다.")
        return {
            "status": "error",
            "message": error_message,
            "data": data
        }