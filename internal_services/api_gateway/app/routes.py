# routers/tickets.py
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from kafka import KafkaProducer
import json
from datetime import datetime
from .config import SECRET_KEY, ALGORITHM, KAFKA_BOOTSTRAP_SERVERS
from .schemas import UseTicketResponse, ReservationRequest

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Kafka 프로듀서 설정
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="유효하지 않은 인증 정보",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
        return {"user_id": user_id, "park_id": payload.get("park_id"), "ticket_type": payload.get("ticket_type")}
    except JWTError:
        raise credentials_exception


@router.post("/reserve_ride/{ride_id}")
async def reserve_ride(ride_id: str, reservation: ReservationRequest, current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    park_id = current_user["park_id"]

    # Kafka 메시지 생성
    message = {
        "event_type": "ride_reservation",
        "user_id": user_id,
        "park_id": park_id,
        "ride_id": ride_id,
        "reservation_time": reservation.reservation_time.isoformat(),
        "timestamp": datetime.utcnow().isoformat()
    }

    # Kafka로 메시지 전송
    producer.send('ride_events', message)

    return {"message": f"Ride {ride_id} reserved for user {user_id}"}

@router.get("/user_info")
async def get_user_info(current_user: dict = Depends(get_current_user)):
    return current_user
