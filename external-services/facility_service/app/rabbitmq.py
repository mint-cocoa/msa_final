import aio_pika
import os
import logging

class RabbitMQConnection:
    _connection = None
    _channel = None
    
    @classmethod
    async def connect(cls):
        if not cls._connection:
            try:
                RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
                cls._connection = await aio_pika.connect_robust(RABBITMQ_URL)
                cls._channel = await cls._connection.channel()
                logging.info("RabbitMQ connection established")
            except Exception as e:
                logging.error(f"Failed to connect to RabbitMQ: {e}")
                raise
    
    @classmethod
    async def get_channel(cls):
        if not cls._channel:
            await cls.connect()
        return cls._channel
    
    @classmethod
    async def close(cls):
        if cls._connection:
            await cls._connection.close()
            cls._connection = None
            cls._channel = None
            logging.info("RabbitMQ connection closed") 