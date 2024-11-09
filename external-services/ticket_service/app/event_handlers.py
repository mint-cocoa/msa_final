import logging
from typing import Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import asyncio

class EventHandler:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.pending = {}  # correlation_id에 따른 응답 저장
        self.lock = asyncio.Lock()

    async def handle_validate_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        티켓 검증 응답을 처리합니다.
        """
        try:
            logging.info(f"Handling ticket validation response: {data}")
            valid = data.get("valid", False)
            message = data.get("message", "")
            ticket_data = data.get("data", {})

            result = {
                "valid": valid,
                "message": message,
                "data": ticket_data
            }

            if not valid:
                logging.warning(f"Ticket validation failed: {message}")
            else:
                logging.info("Ticket validation successful")

            return result

        except Exception as e:
            logging.error(f"Error processing ticket validation response: {e}")
            return {
                "valid": False,
                "message": f"Error processing validation response: {str(e)}",
                "data": {}
            }

    async def handle_purchase_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        티켓 구매 응답을 처리합니다.
        """
        try:
            logging.info(f"Handling ticket purchase response: {data}")
            success = data.get("success", False)
            message = data.get("message", "")
            ticket_data = data.get("data", {})

            if success:
                # 구매 성공 시 DB에 티켓 정보 저장
                ticket_data["created_at"] = datetime.utcnow()
                await self.db.tickets.insert_one(ticket_data)

            return {
                "success": success,
                "message": message,
                "data": ticket_data
            }

        except Exception as e:
            logging.error(f"Error processing ticket purchase response: {e}")
            return {
                "success": False,
                "message": f"Error processing purchase response: {str(e)}",
                "data": {}
            }

    async def handle_cancel_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        티켓 취소 응답을 처리합니다.
        """
        try:
            logging.info(f"Handling ticket cancellation response: {data}")
            success = data.get("success", False)
            message = data.get("message", "")
            ticket_id = data.get("ticket_id")

            if success and ticket_id:
                # 취소 성공 시 DB에서 티켓 상태 업데이트
                await self.db.tickets.update_one(
                    {"_id": ObjectId(ticket_id)},
                    {"$set": {"status": "cancelled", "cancelled_at": datetime.utcnow()}}
                )

            return {
                "success": success,
                "message": message,
                "ticket_id": ticket_id
            }

        except Exception as e:
            logging.error(f"Error processing ticket cancellation response: {e}")
            return {
                "success": False,
                "message": f"Error processing cancellation response: {str(e)}",
                "ticket_id": None
            }

    async def handle_get_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        티켓 조회 응답을 처리합니다.
        """
        try:
            logging.info(f"Handling ticket get response: {data}")
            success = data.get("success", False)
            message = data.get("message", "")
            tickets = data.get("tickets", [])

            return {
                "success": success,
                "message": message,
                "tickets": tickets
            }

        except Exception as e:
            logging.error(f"Error processing ticket get response: {e}")
            return {
                "success": False,
                "message": f"Error processing get response: {str(e)}",
                "tickets": []
            }

    async def handle_error_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        에러 응답을 처리합니다.
        """
        logging.error(f"Handling error response: {data}")
        error_message = data.get("message", "Unknown error occurred")
        return {
            "valid": False,
            "success": False,
            "message": error_message,
            "data": data
        }

    async def wait_for_response(self, correlation_id: str, timeout: int = 30) -> Dict[str, Any]:
        """
        특정 correlation_id에 대한 응답을 기다립니다.
        """
        async with self.lock:
            if correlation_id not in self.pending:
                self.pending[correlation_id] = asyncio.get_event_loop().create_future()

        try:
            response = await asyncio.wait_for(self.pending[correlation_id], timeout=timeout)
            return response
        except asyncio.TimeoutError:
            logging.error(f"Response timeout for correlation_id: {correlation_id}")
            raise TimeoutError("Response timeout")
        finally:
            async with self.lock:
                self.pending.pop(correlation_id, None)

    async def set_response(self, correlation_id: str, response: Dict[str, Any]):
        """
        특정 correlation_id에 대한 응답을 설정합니다.
        """
        async with self.lock:
            if correlation_id in self.pending:
                future = self.pending[correlation_id]
                if not future.done():
                    future.set_result(response)