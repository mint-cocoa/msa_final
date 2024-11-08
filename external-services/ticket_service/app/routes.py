from fastapi import APIRouter, HTTPException, Request, Depends
from .models import CreateTicketForm
from .database import get_db
import logging
import asyncio
from typing import Dict, Any
import uuid

router = APIRouter()

async def wait_for_response(event_handler, timeout: int = 30) -> Dict[str, Any]:
    """응답을 기다리는 유틸리티 함수"""
    start_time = asyncio.get_event_loop().time()
    while asyncio.get_event_loop().time() - start_time < timeout:
        if event_handler.latest_response:
            response = event_handler.latest_response
            event_handler.latest_response = None
            return response
        await asyncio.sleep(0.1)
    raise HTTPException(status_code=408, detail="Response timeout")

@router.post("/tickets/create")
async def create_ticket_endpoint(form: CreateTicketForm, request: Request):
    try:
        validation_data = {
            "action": "validate_facilities",
            "data": {
                "user_id": form.user_id,
                "park_id": form.park_id,
                "ticket_type_name": form.ticket_type_name,
                "facility_ids": form.facility_ids
            }
        }

        # 메시지 발행
        await request.app.state.publisher.publish_and_wait(
            routing_key="structure.validate_facilities",
            data=validation_data,
            timeout=30
        )

        # 응답 대기
        response = await wait_for_response(request.app.state.consumer.event_mapper.event_handler)

        if response.get("status") != "success":
            raise HTTPException(
                status_code=400,
                detail=response.get("message", "시설 유효성 검사 실패")
            )

        return {
            "message": "Ticket created successfully",
            "ticket_id": response.get("ticket_id"),
            "data": response.get("data")
        }

    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="Request timeout")
    except Exception as e:
        logging.error(f"Failed to create ticket: {e}")
        raise HTTPException(status_code=500, detail="Failed to create ticket")