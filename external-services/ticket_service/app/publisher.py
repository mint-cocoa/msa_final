from typing import Optional, Dict, Any
from fastapi import HTTPException
import os
import logging
import aio_pika
import json
from .rabbitmq import RabbitMQClient
import asyncio
import uuid

logger = logging.getLogger(__name__)

class EventPublisher:
    def __init__(self, rabbitmq_url: Optional[str] = None):
        self.rabbitmq_url = rabbitmq_url or os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
        self.client = RabbitMQClient(self.rabbitmq_url)
        self._response = None
        self._response_event = None
        self._connected = False
        logger.info(f"EventPublisher initialized with URL: {self.rabbitmq_url}")

    async def connect(self) -> None:
        try:
            logger.info("Attempting to connect to RabbitMQ...")
            await self.client.connect()
            self._connected = True
            logger.info("Successfully connected to RabbitMQ")
        except Exception as e:
            logger.error(f"RabbitMQ 연결 실패: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail="RabbitMQ 연결 실패")

    async def handle_response(self, message):
        """응답 메시지 처리"""
        try:
            self._response = json.loads(message.decode())
            if self._response_event:
                self._response_event.set()
            logger.info(f"응답 메시지 처리 완료: {self._response}")
        except Exception as e:
            logger.error(f"응답 처리 중 오류 발생: {str(e)}")

    async def create_ticket(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """티켓 생성 메시지 발행 및 응답 대기"""
        try:
            if not self._connected:
                await self.connect()

            # 응답 대기를 위한 이벤트 설정
            self._response = None
            self._response_event = asyncio.Event()
            
            # 응답 큐 설정
            response_queue = await self.client.setup_response_queue(self.handle_response)
            
            # correlation_id 생성
            correlation_id = str(uuid.uuid4())
            
            # 메시지 발행
            await self.client.publish(
                routing_key='ticket.request.create',
                message=data,
                correlation_id=correlation_id,
                reply_to="ticket.response.create"
            )
            logger.info("Ticket creation message published successfully")
            
            # 응답 대기
            try:
                await asyncio.wait_for(self._response_event.wait(), 30)
                return self._response
            except asyncio.TimeoutError:
                logger.error("응답 대기 시간 초과")
                raise HTTPException(status_code=504, detail="응답 대기 시간 초과")
            
        except Exception as e:
            logger.error(f"티켓 생성 메시지 발행 실패: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"티켓 생성 실패: {str(e)}")
        finally:
            self._response_event = None

    async def validate_ticket(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """티켓 검증 메시지 발행 및 응답 대기"""
        try:
            if not self._connected:
                await self.connect()

            # 응답 대기를 위한 이벤트 설정
            self._response = None
            self._response_event = asyncio.Event()
            
            # 응답 큐 설정
            response_queue = await self.client.setup_response_queue(self.handle_response)
            
            # correlation_id 생성
            correlation_id = str(uuid.uuid4())
            
            # 메시지 발행
            await self.client.publish(
                routing_key='ticket.request.validate',
                message=data,
                correlation_id=correlation_id,
                reply_to="ticket.response.validate"
            )
            logger.info("Ticket validation message published successfully")
           
            
        except Exception as e:
            logger.error(f"티켓 검증 메시지 발행 실패: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"티켓 검증 실패: {str(e)}")
        finally:
            self._response_event = None

    async def close(self):
        try:
            await self.client.close()
            self._connected = False
            logger.info("EventPublisher connection closed")
        except Exception as e:
            logger.error(f"RabbitMQ 연결 종료 실패: {str(e)}")
            raise HTTPException(status_code=500, detail="RabbitMQ 연결 종료 실패")