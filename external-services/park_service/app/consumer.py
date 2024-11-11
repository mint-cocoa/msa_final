import aio_pika
import json
import os
import logging
from .event_handlers import EventHandler
from .event_mapping import EventMapper
logger = logging.getLogger(__name__)

class RabbitMQConsumer:
    def __init__(self, rabbitmq_url: str = None):
        self.rabbitmq_url = rabbitmq_url or os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
        self.connection = None
        self.channel = None
        self.exchange = None
        self.event_handler = EventHandler()
        self.event_mapper = EventMapper(self.event_handler)
        logger.info(f"RabbitMQConsumer initialized with URL: {self.rabbitmq_url}")

    async def connect(self):
        try:
            logger.info("Attempting to connect to RabbitMQ...")
            self.connection = await aio_pika.connect_robust(self.rabbitmq_url)
            logger.info("RabbitMQ connection established")
            
            self.channel = await self.connection.channel()
            logger.info("RabbitMQ channel created")
            
            self.exchange = await self.channel.declare_exchange(
                "theme_park_events",
                aio_pika.ExchangeType.TOPIC
            )
            logger.info("Exchange 'theme_park_events' declared")
            
            # 응답 큐 설정
            response_queue = await self.channel.declare_queue(
                "park_response_queue",
                durable=True
            )
            logger.info("Response queue 'park_response_queue' declared")
            
            # 응답 큐 바인딩
            await response_queue.bind(self.exchange, "park.response.#")
            logger.info("Response queue bound to 'park.response.#'")
            
            # 메시지 소비 시작
            await response_queue.consume(self.process_message)
            logger.info("Started consuming messages from response queue")
            
            logger.info("RabbitMQ consumer initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize RabbitMQ consumer: {e}", exc_info=True)
            raise

    async def process_message(self, message: aio_pika.IncomingMessage):
        async with message.process():
            try:
                logger.info(f"Processing message with routing key: {message.routing_key}")
                data = json.loads(message.body.decode())
                logger.debug(f"Received message data: {json.dumps(data, indent=2)}")
                
                # structure_manager로부터 받은 응답 처리
                logger.info("Handling response from structure manager...")
                result = await self.event_mapper.handle_response(message.routing_key, data)
                logger.debug(f"Response handled successfully: {json.dumps(result, indent=2)}")
                
                # 응답이 필요한 경우 처리
                if message.reply_to:
                    logger.info(f"Publishing response to: {message.reply_to}")
                    await self.exchange.publish(
                        aio_pika.Message(
                            body=json.dumps(result).encode(),
                            correlation_id=message.correlation_id,
                            content_type="application/json"
                        ),
                        routing_key=message.reply_to
                    )
                    logger.info("Response published successfully")
                
                logger.info(f"Successfully processed response with routing key: {message.routing_key}")
                
            except Exception as e:
                logger.error(f"Error processing response: {e}", exc_info=True)
                if message.reply_to:
                    logger.info("Sending error response...")
                    error_response = {"error": str(e)}
                    await self.exchange.publish(
                        aio_pika.Message(
                            body=json.dumps(error_response).encode(),
                            correlation_id=message.correlation_id,
                            content_type="application/json"
                        ),
                        routing_key=message.reply_to
                    )
                    logger.info("Error response sent")

    async def close(self):
        try:
            if self.connection:
                logger.info("Closing RabbitMQ connection...")
                await self.connection.close()
                logger.info("RabbitMQ connection closed successfully")
        except Exception as e:
            logger.error(f"Error closing RabbitMQ connection: {e}", exc_info=True)
            raise