import aio_pika
import json
import os
import logging
from .event_handlers import EventHandler
from .event_mapping import EventMapper
from .database import get_db

class RabbitMQConsumer:
    def __init__(self, rabbitmq_url: str = None):
        self.rabbitmq_url = rabbitmq_url or os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
        self.connection = None
        self.channel = None
        self.exchange = None
        self.event_mapper = None
        self.db = None

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

            # Park 서비스 요청을 위한 큐
            park_queue = await self.channel.declare_queue(
                "park_request_queue", 
                durable=True
            )
            
            # Facility 서비스 요청을 위한 큐
            facility_queue = await self.channel.declare_queue(
                "facility_request_queue",
                durable=True
            )
            
            # 토픽 패턴으로 바인딩
            await park_queue.bind(self.exchange, routing_key="park.*")
            await facility_queue.bind(self.exchange, routing_key="facility.*")
            
            # 메시지 소비 시작
            await park_queue.consume(self.process_park_request)
            await facility_queue.consume(self.process_facility_request)
            
            logging.info("Successfully connected to RabbitMQ")
            
        except Exception as e:
            logging.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    async def process_park_request(self, message: aio_pika.IncomingMessage):
        async with message.process():
            try:
                data = json.loads(message.body.decode())
                routing_key = message.routing_key
                
                # Park 서비스 요청 처리
                result = await self.event_mapper.handle_park_request(data)
                
                # 응답 발행
                response_routing_key = f"park.response.{data.get('action', 'unknown')}"
                await self.exchange.publish(
                    aio_pika.Message(
                        body=json.dumps(result).encode(),
                        content_type="application/json"
                    ),
                    routing_key=response_routing_key
                )
                
                logging.info(f"Successfully processed park request: {routing_key}")
                
            except Exception as e:
                logging.error(f"Error processing park request: {e}")
                error_response = {"error": str(e)}
                await self.exchange.publish(
                    aio_pika.Message(
                        body=json.dumps(error_response).encode(),
                        content_type="application/json"
                    ),
                    routing_key="park.response.error"
                )

    async def process_facility_request(self, message: aio_pika.IncomingMessage):
        async with message.process():
            try:
                data = json.loads(message.body.decode())
                routing_key = message.routing_key
                
                # Facility 서비스 요청 처리
                result = await self.event_mapper.handle_facility_request(data)
                
                # 응답 발행
                response_routing_key = f"facility.response.{data.get('action', 'unknown')}"
                await self.exchange.publish(
                    aio_pika.Message(
                        body=json.dumps(result).encode(),
                        content_type="application/json"
                    ),
                    routing_key=response_routing_key
                )
                
                logging.info(f"Successfully processed facility request: {routing_key}")
                
            except Exception as e:
                logging.error(f"Error processing facility request: {e}")
                error_response = {"error": str(e)}
                await self.exchange.publish(
                    aio_pika.Message(
                        body=json.dumps(error_response).encode(),
                        content_type="application/json"
                    ),
                    routing_key="facility.response.error"
                )

    async def close(self):
        if self.connection:
            await self.connection.close()
            