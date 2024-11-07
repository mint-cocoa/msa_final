from .rabbitmq import RabbitMQClient
import os
import asyncio
import json
import logging
from typing import Optional, Dict, Any
import uuid

class EventPublisher:
    def __init__(self, rabbitmq_url: str = None):
        self.rabbitmq_url = rabbitmq_url or os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
        self.client = RabbitMQClient(self.rabbitmq_url)
        self._response = None
        self._response_event = None

    async def connect(self):
        await self.client.connect()
        
    async def handle_response(self, message):
        """응답 메시지 처리"""
        try:
            self._response = json.loads(message.decode())
            if self._response_event:
                self._response_event.set()
        except Exception as e:
            logging.error(f"응답 처리 중 오류 발생: {str(e)}")

    async def publish_and_wait(
        self, 
        routing_key: str, 
        data: Dict[str, Any], 
        timeout: int = 30
    ) -> Optional[Dict[str, Any]]:
        """메시지를 발행하고 응답을 기다림"""
        try:
            # 응답 대기를 위한 이벤트 설정
            self._response = None
            self._response_event = asyncio.Event()
            
            # 응답 큐 설정
            response_queue = await self.client.setup_response_queue(self.handle_response)
            
            # correlation_id 생성
            correlation_id = data.get("correlation_id", str(uuid.uuid4()))
            data["correlation_id"] = correlation_id
            
            # 메시지 발행
            await self.client.publish(
                routing_key=routing_key,
                message=data,
                correlation_id=correlation_id,
                reply_to=response_queue.name
            )
            
            # 응답 대기
            try:
                await asyncio.wait_for(self._response_event.wait(), timeout)
                return self._response
            except asyncio.TimeoutError:
                logging.error("응답 대기 시간 초과")
                raise
                
        except Exception as e:
            logging.error(f"메시지 발행 중 오류 발생: {str(e)}")
            raise
        finally:
            self._response_event = None

    async def close(self):
        await self.client.close() 