import aio_pika
import json
import logging
import uuid
from typing import Optional, Dict
import asyncio

class RabbitMQClient:
    def __init__(self, url: str = "amqp://guest:guest@rabbitmq:5672/"):
        self.url = url
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.exchange: Optional[aio_pika.Exchange] = None
        self.callback_queue: Optional[aio_pika.Queue] = None
        self.futures: Dict[str, asyncio.Future] = {}

    async def connect(self):
        if not self.connection:
            try:
                self.connection = await aio_pika.connect_robust(self.url)
                self.channel = await self.connection.channel()
                self.exchange = await self.channel.declare_exchange(
                    "theme_park_events",
                    aio_pika.ExchangeType.TOPIC
                )
                
                # 응답을 받을 콜백 큐 생성
                self.callback_queue = await self.channel.declare_queue(
                    exclusive=True
                )
                
                await self.callback_queue.consume(self.process_response)
                logging.info("Successfully connected to RabbitMQ")
            except Exception as e:
                logging.error(f"Failed to connect to RabbitMQ: {e}")
                raise

    async def process_response(self, message: aio_pika.IncomingMessage):
        async with message.process():
            correlation_id = message.correlation_id
            if correlation_id in self.futures:
                future = self.futures.pop(correlation_id)
                response = json.loads(message.body.decode())
                future.set_result(response)

    async def publish(self, routing_key: str, message: dict):
        if not self.exchange:
            await self.connect()
        
        try:
            await self.exchange.publish(
                aio_pika.Message(
                    body=json.dumps(message).encode(),
                    content_type="application/json"
                ),
                routing_key=routing_key
            )
        except Exception as e:
            logging.error(f"Failed to publish message: {e}")
            raise

    async def rpc_call(self, routing_key: str, message: dict, timeout: int = 30) -> dict:
        if not self.exchange:
            await self.connect()

        correlation_id = str(uuid.uuid4())
        future = asyncio.Future()
        self.futures[correlation_id] = future

        try:
            await self.exchange.publish(
                aio_pika.Message(
                    body=json.dumps(message).encode(),
                    content_type="application/json",
                    correlation_id=correlation_id,
                    reply_to=self.callback_queue.name,
                ),
                routing_key=routing_key
            )

            # 타임아웃과 함께 응답 대기
            return await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError:
            self.futures.pop(correlation_id, None)
            raise HTTPException(status_code=408, detail="Request timeout")
        except Exception as e:
            self.futures.pop(correlation_id, None)
            logging.error(f"RPC call failed: {e}")
            raise

    async def close(self):
        if self.connection:
            await self.connection.close()
            self.connection = None
            self.channel = None
            self.exchange = None