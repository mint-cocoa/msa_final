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

    async def connect(self):
        try:
            await self.client.connect()
            self._connected = True
            logger.info("EventPublisher connected to RabbitMQ")
        except Exception as e:
            logger.error(f"RabbitMQ 연결 실패: {str(e)}")
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
            logger.info(f"응답 대기를 위한 이벤트 설정: routing_key={routing_key}, data={data}")
            
            # 응답 큐 설정
            response_queue = await self.client.setup_response_queue(self.handle_response)
            logger.info(f"응답 큐 설정 완료: {response_queue.name}")
            
            # correlation_id 생성
            correlation_id = data.get("correlation_id", str(uuid.uuid4()))
            data["correlation_id"] = correlation_id
            logger.debug(f"Correlation ID 생성: {correlation_id}")
            
            # 메시지 발행
            await self.client.publish(
                routing_key=routing_key,
                message=data,
                correlation_id=correlation_id,
                reply_to=response_queue.name
            )
            logger.info(f"메시지 발행 완료: routing_key={routing_key}, correlation_id={correlation_id}")
            
            # 응답 대기
            try:
                await asyncio.wait_for(self._response_event.wait(), timeout)
                logger.info(f"응답 수신 완료: {self._response}")
                return self._response
            except asyncio.TimeoutError:
                logger.error("응답 대기 시간 초과")
                raise HTTPException(status_code=504, detail="응답 대기 시간 초과")
                
        except Exception as e:
            logger.error(f"메시지 발행 중 오류 발생: {str(e)}")
            raise HTTPException(status_code=500, detail="메시지 발행 중 오류 발생")
        finally:
            self._response_event = None
            logger.debug("응답 이벤트 초기화")

    async def publish_structure_update(self, data: Dict[str, Any]) -> None:
        if not self._connected:
            await self.connect()
        try:
            await self.client.publish('structure.update', data)
            logger.info("구조 업데이트 메시지 발행 성공")
        except Exception as e:
            logger.error(f"구조 업데이트 발행 실패: {str(e)}")
            raise HTTPException(status_code=500, detail="구조 업데이트 발행 실패")
        
    async def publish_ticket_validation_result(self, result: Dict[str, Any]) -> None:
        logger.info(f"티켓 유효성 검사 결과 발행: {result}")
        try:
            await self.client.publish('ticket.validate', result)
            logger.info("티켓 유효성 검사 결과 발행 성공")
        except Exception as e:
            logger.error(f"티켓 유효성 검사 결과 발행 실패: {str(e)}")
            raise HTTPException(status_code=500, detail="티켓 유효성 검사 결과 발행 실패")

    async def close(self):                                 
        try:
            await self.client.close()
            self._connected = False
            logger.info("EventPublisher connection closed")
        except Exception as e:
            logger.error(f"RabbitMQ 연결 종료 실패: {str(e)}")
            raise HTTPException(status_code=500, detail="RabbitMQ 연결 종료 실패")