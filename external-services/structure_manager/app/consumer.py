import aio_pika
import json
from .database import get_db
import os
import logging
from .event_handlers import EventHandler
from .event_mapping import EventMapper

class RabbitMQConsumer:
    def __init__(self, rabbitmq_url: str = None):
        self.rabbitmq_url = rabbitmq_url or os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
        self.connection = None
        self.channel = None
        self.exchange = None
        self.db = None
        self.event_mapper = None

    async def connect(self):
        try:
            self.connection = await aio_pika.connect_robust(self.rabbitmq_url)
            self.channel = await self.connection.channel()
            self.exchange = await self.channel.declare_exchange(
                "theme_park_events",
                aio_pika.ExchangeType.TOPIC
            )
            self.db = await get_db()
            
            # 이벤트 핸들러와 매퍼 초기화
            event_handler = EventHandler(self.db)
            self.event_mapper = EventMapper(event_handler)

            # 일반 업데이트용 큐
            update_queue = await self.channel.declare_queue(
                "structure_manager_updates", 
                durable=True
            )
            
            # RPC 요청용 큐
            rpc_queue = await self.channel.declare_queue(
                "structure_manager_rpc",
                durable=True
            )
            
            # 토픽 패턴으로 바인딩
            await update_queue.bind(self.exchange, routing_key="*.updates.*")
            await rpc_queue.bind(self.exchange, routing_key="*.create")
            
            await update_queue.consume(self.process_update)
            await rpc_queue.consume(self.process_rpc)
            logging.info("Successfully connected to RabbitMQ")
            
        except Exception as e:
            logging.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    async def process_update(self, message: aio_pika.IncomingMessage):
        async with message.process():
            try:
                data = json.loads(message.body.decode())
                routing_key = message.routing_key
                await self.event_mapper.route_event(routing_key, data)
            except Exception as e:
                logging.error(f"Error processing update message: {e}")

    async def process_rpc(self, message: aio_pika.IncomingMessage):
        async with message.process():
            try:
                data = json.loads(message.body.decode())
                routing_key = message.routing_key
                
                # RPC 요청 처리
                result = await self.event_mapper.handle_rpc(routing_key, data)
                
                # 응답 전송
                await self.exchange.publish(
                    aio_pika.Message(
                        body=json.dumps(result).encode(),
                        correlation_id=message.correlation_id,
                        content_type="application/json"
                    ),
                    routing_key=message.reply_to
                )
            except Exception as e:
                logging.error(f"Error processing RPC message: {e}")
                # 에러 응답 전송
                error_response = {
                    "error": str(e)
                }
                await self.exchange.publish(
                    aio_pika.Message(
                        body=json.dumps(error_response).encode(),
                        correlation_id=message.correlation_id,
                        content_type="application/json"
                    ),
                    routing_key=message.reply_to
                )

    async def close(self):
        if self.connection:
            await self.connection.close()
            