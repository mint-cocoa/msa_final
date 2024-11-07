from fastapi import APIRouter, Depends, HTTPException
from .models import CreateTicketForm
from .database import get_db
from .publisher import EventPublisher
from .event_handlers import EventHandler
from .event_mapping import EventMapper
import logging
from datetime import datetime
import asyncio
import uuid

router = APIRouter()

@router.post("/")
async def create_ticket_endpoint(form: CreateTicketForm, db = Depends(get_db)):
    try:
        # 이벤트 핸들러 및 매퍼 초기화
        event_handler = EventHandler(db)
        event_mapper = EventMapper(event_handler)
        
        # 이벤트 발행자 초기화
        publisher = EventPublisher()
        await publisher.connect()

        # Structure Manager에 시설 유효성 검사 요청
        validation_data = {
            "action": "validate_facilities",
            "data": {
                "user_id": form.user_id,
                "park_id": form.park_id,
                "ticket_type_name": form.ticket_type_name,
                "facility_ids": form.facility_ids
            }
        }

        # 시설 유효성 검사 이벤트 발행 및 응답 대기
        response = await publisher.publish_and_wait(
            exchange="structure_exchange",
            routing_key="structure.validate_facilities",
            data=validation_data,
            reply_to="ticket_response_queue",
            correlation_id=str(uuid.uuid4()),
            timeout=30
        )

        # 응답 처리
        result = await event_mapper.handle_response(
            routing_key="ticket.response.validate_access",
            data=response
        )

        if result.get("status") != "success":
            raise HTTPException(
                status_code=400,
                detail=result.get("message", "시설 유효성 검사 실패")
            )

        return {
            "status": "success",
            "ticket_id": result.get("ticket_id"),
            "message": result.get("message"),
            "data": result.get("data")
        }

    except asyncio.TimeoutError:
        logging.error("시설 유효성 검사 요청 시간 초과")
        raise HTTPException(status_code=408, detail="요청 시간이 초과되었습니다.")
    except Exception as e:
        logging.error(f"티켓 생성 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail="티켓 생성 중 오류가 발생했습니다.")
    finally:
        if publisher:
            await publisher.close()

