from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from .schemas import CreateTicketForm, TicketResponse, TicketUseResponse
from .database import users_collection, parks_collection, ticket_collection
from .utils import create_ticket, create_access_token
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from .config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(
    prefix="/tickets",
    tags=["Tickets"]
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.post("/create_ticket", response_model=TicketResponse)
def create_ticket_endpoint(form: CreateTicketForm):
    # 사용자 정보를 가져옵니다.
    user = users_collection.find_one({"_id": ObjectId(form.user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    # 공원 컬렉션에서 park_ticket_id를 가진 티켓을 찾습니다.
    park = parks_collection.find_one({
        "tickets._id": ObjectId(form.park_ticket_id)
    })
    if not park:
        raise HTTPException(status_code=404, detail="공원 또는 티켓을 찾을 수 없습니다.")

    # 해당 티켓 정보를 가져옵니다.
    park_ticket = next((ticket for ticket in park.get('tickets', []) if ticket['_id'] == ObjectId(form.park_ticket_id)), None)
    if not park_ticket:
        raise HTTPException(status_code=404, detail="티켓을 찾을 수 없습니다.")

    # 티켓 생성
    ticket_data = {
        "user_id": form.user_id,
        "park_id": str(park['_id']),
        "park_ticket_data": park_ticket,
        "purchase_date": datetime.utcnow().isoformat(),
        "amount": park_ticket['price'],
        "available_date": form.available_date,
        "used": False
    }

    result = create_ticket(ticket_data)

    return {
        "ticket_id": str(result.inserted_id),
        "message": "티켓이 성공적으로 생성되었습니다."
    }

@router.post("/use/{ticket_id}", response_model=TicketUseResponse)
async def use_ticket(ticket_id: str):
    ticket = ticket_collection.find_one({"_id": ObjectId(ticket_id)})
    if not ticket:
        raise HTTPException(status_code=404, detail="티켓을 찾을 수 없습니다.")
    if ticket["used"]:
        raise HTTPException(status_code=400, detail="이미 사용된 티켓입니다.")
    
    # 티켓 사용 처리
    ticket_collection.update_one({"_id": ObjectId(ticket_id)}, {"$set": {"used": True, "used_at": datetime.utcnow()}})
    
    # JWT 토큰 생성
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": str(ticket["_id"]),
            "user_id": ticket["user_id"],
            "park_id": ticket["park_id"],
            "ticket_type": ticket["park_ticket_data"]["type"]
        },
        expires_delta=access_token_expires
    )
    
    return {"message": "티켓이 성공적으로 사용되었습니다.", "access_token": access_token, "token_type": "bearer"}

@router.get("/verify_ticket")
async def verify_ticket(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        ticket_id = payload.get("sub")
        if ticket_id is None:
            raise HTTPException(status_code=401, detail="유효하지 않은 티켓입니다.")
        
        # 여기에서 티켓의 유효성을 추가로 확인할 수 있습니다 (예: 데이터베이스에서 티켓 상태 확인)
        ticket = ticket_collection.find_one({"_id": ObjectId(ticket_id)})
        if not ticket or ticket["used"] == False:
            raise HTTPException(status_code=401, detail="유효하지 않은 티켓입니다.")
        
        return {"message": "유효한 티켓입니다.", "ticket_data": payload}
    except JWTError:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")
