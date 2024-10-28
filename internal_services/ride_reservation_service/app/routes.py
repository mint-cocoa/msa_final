from fastapi import APIRouter, HTTPException, Depends, Request
from .dependencies import get_current_user
from .rabbitmq_publisher import publish_reservation_request
import os
from .utils import verify_ticket
from fastapi.security import OAuth2PasswordBearer
router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
REDIS_SERVICE_URL = os.getenv("REDIS_SERVICE_URL", "http://redis-service:8000")

@router.post("/reserve/{ride_id}")
async def reserve_ride(ride_id: str, request: Request, token: str = Depends(oauth2_scheme)):
    user_id = await verify_ticket(token)
    await publish_reservation_request(request.app.state.rabbitmq_channel, user_id, ride_id)
    return {"message": f"User {user_id} reservation request for ride {ride_id} has been sent."}
# 테스트 엔드포인트 추가
@router.get("/dev/reserve/{user_id}")
async def test_endpoint(user_id: str, request: Request):
    # RabbitMQ에 예약 요청 메시지 발행
    await publish_reservation_request(request.app.state.rabbitmq_channel, user_id, "1234")
    return {"message": f"User {user_id} reservation request has been sent."}
