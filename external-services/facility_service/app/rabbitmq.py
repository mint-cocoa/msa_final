import os
import uuid
import json
import logging
import aio_pika
from typing import Optional, Callable, Any

logger = logging.getLogger(__name__)

class RabbitMQClient:
    def __init__(self, url: str = "amqp://guest:guest@rabbitmq:5672/"):
        self.url = url
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.exchange: Optional[aio_pika.Exchange] = None
        self.response_queue: Optional[aio_pika.Queue] = None

    async def connect(self):
        if not self.connection:
            try:
                self.connection = await aio_pika.connect_robust(self.url)
                self.channel = await self.connection.channel()
                self.exchange = await self.channel.declare_exchange(
                    "theme_park_events",
                    aio_pika.ExchangeType.TOPIC
                )
                logger.info("Successfully connected to RabbitMQ")
            except Exception as e:
                logger.error(f"Failed to connect to RabbitMQ: {e}")
                raise

    async def setup_response_queue(self, callback: Callable[[bytes], Any]) -> aio_pika.Queue:
        """응답을 받기 위한 임시 큐 설정"""
        try:
            if not self.channel:
                await self.connect()
            
            # 임시 응답 큐 생성
            self.response_queue = await self.channel.declare_queue(
                f"response_queue_{uuid.uuid4()}",
                auto_delete=True
            )
            
            # 콜백 설정
            await self.response_queue.consume(
                lambda message: self._handle_response(message, callback)
            )
            
            return self.response_queue
            
        except Exception as e:
            logger.error(f"Failed to setup response queue: {e}")
            raise

    async def _handle_response(self, message: aio_pika.IncomingMessage, callback: Callable[[bytes], Any]):
        """응답 메시지 처리"""
        async with message.process():
            try:
                await callback(message.body)
            except Exception as e:
                logger.error(f"Error handling response: {e}")

    async def publish(self, routing_key: str, message: dict, correlation_id: str = None, reply_to: str = None):
        """메시지 발행"""
        try:
            if not self.channel:
                await self.connect()

            message_body = json.dumps(message).encode()
            
            # 메시지 속성 설정
            message_properties = {}
            if correlation_id:
                message_properties['correlation_id'] = correlation_id
            if reply_to:
                message_properties['reply_to'] = reply_to

            # 메시지 발행
            await self.exchange.publish(
                aio_pika.Message(
                    body=message_body,
                    content_type='application/json',
                    **message_properties
                ),
                routing_key=routing_key
            )
            logger.info(f"Message published successfully to {routing_key}")
            
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            raise

    async def close(self):
        """RabbitMQ 연결 종료"""
        try:
            if self.connection:
                await self.connection.close()
                logger.info("RabbitMQ connection closed")
        except Exception as e:
            logger.error(f"Error closing RabbitMQ connection: {e}")
            raise