from fastapi import APIRouter, HTTPException, Request, Depends
from .models import TicketValidationModel
from .database import get_db
import logging
import asyncio
from typing import Dict, Any
import uuid

router = APIRouter()

async def wait_for_response(event_handler, timeout: int = 30) -> Dict[str, Any]:
    """응답을 기다리는 유틸리티 함수"""
    start_time = asyncio.get_event_loop().time()
    logging.info(f"waiting for response: {event_handler}")
    while asyncio.get_event_loop().time() - start_time < timeout:
        if event_handler.latest_response:
            response = event_handler.latest_response
            event_handler.latest_response = None
            return response
        await asyncio.sleep(0.1)
    raise HTTPException(status_code=408, detail="Response timeout")

@router.post("/tickets/validate")
async def validate_ticket_endpoint(form: TicketValidationModel, request: Request):
    try:    
        await request.app.state.publisher.publish_ticket_validation({
            "action": "validate",
             "data": {
                "user_id": form.user_id,
                "park_id": form.park_id,
                "ticket_type_name": form.ticket_type_name,
                "facility_ids": form.facility_ids
            }
        })
        response = await wait_for_response(request.app.state.consumer.event_handler)
        return response
    except Exception as e:
        logging.error(f"Failed to send ticket validation event: {e}")
        raise HTTPException(status_code=500, detail="Failed to validate ticket")
