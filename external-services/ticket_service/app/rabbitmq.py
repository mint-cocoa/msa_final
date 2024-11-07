import aio_pika
import json
import logging
import uuid
from typing import Optional, Dict, Callable
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

    async def setup_response_queue(self, callback: Callable) -> aio_pika.Queue:
        """응답을 받기 위한 임시 큐 설정"""
        if not self.channel:
            await self.connect()
            
        # 임시 큐 생성
        queue = await self.channel.declare_queue(
            "",  # 빈 이름으로 설정하면 RabbitMQ가 임의의 이름 생성
            auto_delete=True  # 연결이 종료되면 큐 자동 삭제
        )
        
        # 메시지 소비 설정
        await queue.consume(lambda message: self._process_response(message, callback))
        
        return queue

    async def _process_response(self, message: aio_pika.IncomingMessage, callback: Callable):
        """응답 메시지 처리"""
        async with message.process():
            await callback(message.body)

    async def publish(
        self, 
        routing_key: str, 
        message: dict,
        correlation_id: str = None,
        reply_to: str = None
    ):
        if not self.exchange:
            await self.connect()
        
        try:
            await self.exchange.publish(
                aio_pika.Message(
                    body=json.dumps(message).encode(),
                    content_type="application/json",
                    correlation_id=correlation_id,
                    reply_to=reply_to
                ),
                routing_key=routing_key
            )
        except Exception as e:
            logging.error(f"Failed to publish message: {e}")
            raise

    async def close(self):
        if self.connection:
            await self.connection.close()
            self.connection = None
            self.channel = None
            self.exchange = None