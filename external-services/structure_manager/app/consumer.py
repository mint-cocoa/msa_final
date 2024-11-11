import aio_pika
import json
import os
import logging
from .event_handlers import EventHandler
from .event_mapping import EventMapper
from .database import get_db

class RabbitMQConsumer:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.exchange = None
        self.event_handler = None
        self.event_mapper = None
        logging.info("RabbitMQConsumer initialized")

    async def connect(self):
        try:
            logging.info("Attempting to connect to RabbitMQ...")
            
            # RabbitMQ 연결 설정
            self.connection = await aio_pika.connect_robust(
                os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
            )
            logging.info("RabbitMQ connection established")
            
            self.channel = await self.connection.channel()
            logging.info("RabbitMQ channel created")
            
            # 교환기 선언
            self.exchange = await self.channel.declare_exchange(
                "theme_park_events",
                aio_pika.ExchangeType.TOPIC
            )
            
            # 요청 큐 설정
            request_queue = await self.channel.declare_queue(
                "structure_request_queue", 
                durable=True
            )
            
            # 요청 큐 바인딩
            await request_queue.bind(self.exchange, "park.request.#")
            await request_queue.bind(self.exchange, "facility.request.#")
            await request_queue.bind(self.exchange, "ticket.request.#")
            
            # 이벤트 핸들러 초기화
            structure_db = await get_db('structure')
            self.event_handler = EventHandler(structure_db)
            await self.event_handler.initialize_dbs()
            self.event_mapper = EventMapper(self.event_handler)
            
            # 메시지 소비 시작
            await request_queue.consume(self.process_message)
            
            logging.info("RabbitMQ consumer initialized successfully")
            
        except Exception as e:
            logging.error(f"Failed to initialize RabbitMQ consumer: {e}")
            raise

    async def process_message(self, message: aio_pika.IncomingMessage):
        async with message.process():
            try:
                logging.info(f"Processing message with routing key: {message.routing_key}")
                data = json.loads(message.body.decode())
                logging.info(f"Message data: {json.dumps(data, indent=2)}")
                
                # Structure 서비스 요청 처리
                logging.info("Handling structure request...")
                result = await self.event_mapper.handle_request(message.routing_key, data)
                logging.info(f"Request handled successfully: {json.dumps(result, indent=2)}")
                
                # 응답 발행
                if message.reply_to:
                    logging.info(f"Sending response to: {message.reply_to}")
                    logging.info(f"Response: {json.dumps(result, indent=2)}")
                    await self.exchange.publish(
                        aio_pika.Message(
                            body=json.dumps(result).encode(),
                            content_type="application/json",
                            correlation_id=message.correlation_id
                        ),
                        routing_key=message.reply_to
                    )
                    logging.info(f"Response sent successfully for routing key: {message.routing_key}")
                
            except Exception as e:
                logging.error(f"Error processing message: {str(e)}")
                logging.error(f"Message routing key: {message.routing_key}")
                logging.error(f"Message body: {message.body.decode()}")
                if message.reply_to:
                    error_response = {
                        "valid": False,
                        "message": str(e),
                        "data": {}
                    }
                    logging.info(f"Sending error response to: {message.reply_to}")
                    await self.exchange.publish(
                        aio_pika.Message(
                            body=json.dumps(error_response).encode(),
                            content_type="application/json",
                            correlation_id=message.correlation_id
                        ),
                        routing_key=message.reply_to
                    )
                    logging.info("Error response sent successfully")

    async def close(self):
        if self.connection:
            logging.info("Closing RabbitMQ connection...")
            await self.connection.close()
            logging.info("RabbitMQ connection closed")
            