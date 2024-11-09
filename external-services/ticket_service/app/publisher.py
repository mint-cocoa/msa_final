from typing import Optional, Dict, Any
from .rabbitmq import RabbitMQClient
from fastapi import HTTPException
import os
import logging

logger = logging.getLogger(__name__)

class EventPublisher:
    def __init__(self, rabbitmq_url: Optional[str] = None):
        self.rabbitmq_url = rabbitmq_url or os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
        self.client = RabbitMQClient(self.rabbitmq_url)
        self._connected = False

    async def connect(self) -> None:
        try:
            await self.client.connect()
            self._connected = True
        except Exception as e:
            logger.error(f"RabbitMQ 연결 실패: {str(e)}")
            raise HTTPException(status_code=500, detail="RabbitMQ 연결 실패")

    async def publish_ticket_validation(self, data: Dict[str, Any]) -> None:
        if not self._connected:
            await self.connect()
        try:
            await self.client.publish('ticket.validate', data)
        except Exception as e:
            logger.error(f"ticket validation publish error: {str(e)}")      
            raise HTTPException(status_code=500, detail="ticket validation publish error")
         
    async def close(self) -> None:
        if self._connected:
            try:
                await self.client.close()
                self._connected = False
            except Exception as e:
                logger.error(f"RabbitMQ 연결 종료 실패: {str(e)}")
                raise HTTPException(status_code=500, detail="RabbitMQ 연결 종료 실패")