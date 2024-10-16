from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import requests
from . import schemas, models, crud
from .database import get_db
from .dependencies import get_current_active_user

router = APIRouter()

TICKET_SERVICE_URL = "http://ticket_service:8004/api/tickets"

@router.post("/purchase", response_model=schemas.PurchaseResponse)
def purchase_tickets(
    purchase: schemas.PurchaseRequest,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # URI에서 온 정보 검증
    if purchase.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="본인만 티켓을 구매할 수 있습니다.")
    
    total_price = 0.0
    detailed_items = []
    
    for item in purchase.items:
        # 각 티켓 타입의 가격을 ticket_service에서 가져오기
        ticket_type_response = requests.get(f"http://ticket_service:8004/api/ticket-types/{item.ticket_type_id}")
        
        if ticket_type_response.status_code != 200:
            raise HTTPException(status_code=404, detail=f"티켓 타입 ID {item.ticket_type_id}을 찾을 수 없습니다.")
        
        ticket_type = ticket_type_response.json()
        item_price = ticket_type["price"] * item.quantity
        total_price += item_price
        detailed_items.append({
            "ticket_type_id": item.ticket_type_id,
            "quantity": item.quantity,
            "price": item_price
        })
    
    # 추가 정보 가져오기
    user_response = requests.get(f"http://user_service:8001/api/users/{purchase.user_id}")
    if user_response.status_code != 200:
        raise HTTPException(status_code=404, detail="사용자 정보를 가져올 수 없습니다.")
    user_info = user_response.json()
    
    park_response = requests.get(f"http://park_service:8002/api/parks/{purchase.park_id}")
    if park_response.status_code != 200:
        raise HTTPException(status_code=404, detail="공원 정보를 가져올 수 없습니다.")
    park_info = park_response.json()
    
    facility_response = requests.get(f"http://facility_service:8003/api/facilities/{purchase.facility_id}")
    if facility_response.status_code != 200:
        raise HTTPException(status_code=404, detail="시설 정보를 가져올 수 없습니다.")
    facility_info = facility_response.json()
    
    # 티켓 발급 (ticket_service에 요청)
    ticket_data = {
        "user_id": purchase.user_id,
        "park_id": purchase.park_id,
        "facility_id": purchase.facility_id,
        "items": detailed_items,
        "total_price": total_price,
        "user_info": user_info,
        "park_info": park_info,
        "facility_info": facility_info
    }
    
    ticket_response = requests.post("http://ticket_service:8004/api/tickets", json=ticket_data)
    
    if ticket_response.status_code != 200:
        raise HTTPException(status_code=500, detail="티켓 발급에 실패했습니다.")
    
    ticket_info = ticket_response.json()
    
    # 구매 정보 저장
    db_purchase = crud.create_purchase(db, purchase, total_price)
    for item in purchase.items:
        ticket_type_response = requests.get(f"http://ticket_service:8004/api/ticket-types/{item.ticket_type_id}")
        ticket_type = ticket_type_response.json()
        crud.create_purchase_item(db, db_purchase.id, item, ticket_type["price"])
    
    return schemas.PurchaseResponse(
        purchase_id=db_purchase.id,
        user_id=db_purchase.user_id,
        park_id=purchase.park_id,
        facility_id=purchase.facility_id,
        items=purchase.items,
        total_price=db_purchase.total_price,
        purchased_at=db_purchase.purchased_at,
        user_info=user_info,
        park_info=park_info,
        facility_info=facility_info
    )
