import json
import logging
import aio_pika
from .event_handlers import EventHandler
from .database import get_db
import os

class RabbitMQConsumer:
    def __init__(self, rabbitmq_url: str):
        self.rabbitmq_url = rabbitmq_url or os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
        self.exchange = None
        self.event_handler = None

    async def connect(self):
        try:
            self.connection = await aio_pika.connect_robust(self.rabbitmq_url)
            self.channel = await self.connection.channel()
            self.exchange = await self.channel.declare_exchange(
                "theme_park_events",
                aio_pika.ExchangeType.TOPIC
            )
            
            self.db = get_db()
            self.event_handler = EventHandler(self.db)

            # 티켓 응답을 위한 큐 선언 및 바인딩
            response_queue = await self.channel.declare_queue(
                "ticket_response_queue",
                durable=True
            )
            await response_queue.bind(self.exchange, routing_key="ticket.response.*")
            
            # 메시지 소비 시작
            await response_queue.consume(self.process_message)
            
            logging.info("Ticket Service RabbitMQ 연결 및 응답 큐 소비 시작 완료")
        except Exception as e:
            logging.error(f"RabbitMQ 연결 실패: {e}")
            raise

    async def process_message(self, message: aio_pika.IncomingMessage):
        async with message.process():
            try:
                data = json.loads(message.body.decode())
                routing_key = message.routing_key
                
                # EventMapper를 통해 응답 처리
                from .event_mapping import EventMapper
                event_mapper = EventMapper(self.event_handler)
                result = await event_mapper.handle_ticket_response(routing_key, data)
                
                # 응답 설정
                await self.event_handler.set_response(result)
                
                logging.info(f"Successfully processed response with routing key: {routing_key}")
                
            except Exception as e:
                logging.error(f"Error processing response: {e}")
                error_response = {"error": str(e)}
                await self.event_handler.set_response(error_response)

    async def close(self):
        if self.connection:
            await self.connection.close()
            