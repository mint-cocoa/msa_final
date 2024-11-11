import aio_pika
import json
import logging
import uuid
from typing import Optional, Dict, Callable, Any
import asyncio

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
                logging.info("Successfully connected to RabbitMQ")
            except Exception as e:
                logging.error(f"Failed to connect to RabbitMQ: {e}")
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
            logging.error(f"Failed to setup response queue: {e}")
            raise

    async def _handle_response(self, message: aio_pika.IncomingMessage, callback: Callable[[bytes], Any]):
        """응답 메시지 처리"""
        async with message.process():
            await callback(message.body)

    async def publish(self, routing_key: str, message: dict, correlation_id: str = None, reply_to: str = None):
        if not self.exchange:
            await self.connect()
        
        try:
            message_kwargs = {
                "body": json.dumps(message).encode(),
                "content_type": "application/json",
            }
            
            if correlation_id:
                message_kwargs["correlation_id"] = correlation_id
            if reply_to:
                message_kwargs["reply_to"] = reply_to
                
            await self.exchange.publish(
                aio_pika.Message(**message_kwargs),
                routing_key=routing_key
            )
        except Exception as e:
            logging.error(f"Failed to publish message: {e}")
            raise

    async def close(self):
        """RabbitMQ 연결 종료"""
        try:
            if self.response_queue:
                await self.response_queue.delete()
            if self.connection:
                await self.connection.close()
        except Exception as e:
            logging.error(f"Failed to close RabbitMQ connection: {e}")
            raise