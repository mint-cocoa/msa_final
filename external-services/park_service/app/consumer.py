import aio_pika
import json
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
        self.event_mapper = None

    async def connect(self):
        try:
            self.connection = await aio_pika.connect_robust(self.rabbitmq_url)
            self.channel = await self.connection.channel()
            self.exchange = await self.channel.declare_exchange(
                "theme_park_events",
                aio_pika.ExchangeType.TOPIC
            )
            
            # 이벤트 핸들러와 매퍼 초기화
            event_handler = EventHandler()
            self.event_mapper = EventMapper(event_handler)

            # Park 관련 응답을 위한 큐
            park_queue = await self.channel.declare_queue(
                "park_service_queue", 
                durable=True
            )
            
            # 토픽 패턴으로 바인딩 (park 관련 모든 응답)
            await park_queue.bind(self.exchange, routing_key="park.response.*")
            
            # 메시지 소비 시작
            await park_queue.consume(self.process_message)
            logging.info("Successfully connected to RabbitMQ")
            
        except Exception as e:
            logging.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    async def process_message(self, message: aio_pika.IncomingMessage):
        async with message.process():
            try:
                data = json.loads(message.body.decode())
                routing_key = message.routing_key
                
                # structure_manager로부터 받은 응답 처리
                result = await self.event_mapper.handle_response(routing_key, data)
                
                # 응답이 필요한 경우 처리
                if message.reply_to:
                    await self.exchange.publish(
                        aio_pika.Message(
                            body=json.dumps(result).encode(),
                            correlation_id=message.correlation_id,
                            content_type="application/json"
                        ),
                        routing_key=message.reply_to
                    )
                
                logging.info(f"Successfully processed response with routing key: {routing_key}")
                
            except Exception as e:
                logging.error(f"Error processing response: {e}")
                if message.reply_to:
                    error_response = {"error": str(e)}
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