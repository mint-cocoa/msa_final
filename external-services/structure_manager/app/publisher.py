from typing import Optional, Dict, Any
from fastapi import HTTPException
import os
import logging
import aio_pika
import json

logger = logging.getLogger(__name__)

class EventPublisher:
    def __init__(self, rabbitmq_url: Optional[str] = None):
        self.rabbitmq_url = rabbitmq_url or os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
        self.connection = None
        self.channel = None
        self.exchange = None

    async def connect(self) -> None:
        try:
            if not self.connection:
                self.connection = await aio_pika.connect_robust(self.rabbitmq_url)
                self.channel = await self.connection.channel()
                self.exchange = await self.channel.declare_exchange(
                    "theme_park_events",
                    aio_pika.ExchangeType.TOPIC
                )
        except Exception as e:
            logger.error(f"RabbitMQ 연결 실패: {str(e)}")
            raise HTTPException(status_code=500, detail="RabbitMQ 연결 실패")

    async def publish_query(self, data: Dict[str, Any]) -> None:
        if not self.exchange:
            await self.connect()
        try:
            await self.exchange.publish(
                aio_pika.Message(
                    body=json.dumps(data).encode(),
                    content_type="application/json"
                ),
                routing_key="structure.query"
            )
        except Exception as e:
            logger.error(f"쿼리 요청 발행 실패: {str(e)}")
            raise HTTPException(status_code=500, detail="쿼리 요청 발행 실패")

    async def close(self) -> None:
        if self.connection:
            try:
                await self.connection.close()
                self.connection = None
                self.channel = None
                self.exchange = None
            except Exception as e:
                logger.error(f"RabbitMQ 연결 종료 실패: {str(e)}")
                raise HTTPException(status_code=500, detail="RabbitMQ 연결 종료 실패") 