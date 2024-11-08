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
            # 데이터베이스 연결
            self.db = get_db()
            
            # RabbitMQ 연결
            self.connection = await aio_pika.connect_robust(self.rabbitmq_url)
            self.channel = await self.connection.channel()
            self.exchange = await self.channel.declare_exchange(
                "theme_park_events",
                aio_pika.ExchangeType.TOPIC
            )
            
            # 이벤트 핸들러와 매퍼 초기화 (DB 전달)
            event_handler = EventHandler(self.db)
            self.event_mapper = EventMapper(event_handler)

            # 티켓 서비스 응답을 위한 큐
            ticket_queue = await self.channel.declare_queue(
                "ticket_response_queue", 
                durable=True
            )
            
            # 티켓 관련 응답에 대한 바인딩
            await ticket_queue.bind(self.exchange, routing_key="ticket.response.*")
            
            # 메시지 소비 시작
            await ticket_queue.consume(self.process_message)
            logging.info("Successfully connected to RabbitMQ and initialized ticket service consumer")
            
        except Exception as e:
            logging.error(f"Failed to initialize ticket service consumer: {e}")
            raise

    async def process_message(self, message: aio_pika.IncomingMessage):
        async with message.process():
            try:
                data = json.loads(message.body.decode())
                routing_key = message.routing_key
                
                # 티켓 서비스 응답 처리
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
                
                logging.info(f"Successfully processed ticket service response: {routing_key}")
                
            except Exception as e:
                logging.error(f"Error processing ticket service response: {e}")
                if message.reply_to:
                    error_response = {
                        "status": "error",
                        "message": f"티켓 처리 중 오류 발생: {str(e)}"
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