from fastapi import APIRouter, HTTPException, Depends, Request
from .models import ParkStructureTreeNode, TicketTypeAccess, NodeCreate
from .database import get_db
from bson import ObjectId
from typing import List
import asyncio
from datetime import datetime
import httpx
import os

# 환경 변수 추가
RESERVATION_SERVICE_URL = os.getenv('RESERVATION_SERVICE_URL', 'http://localhost:8001')
TICKET_SERVICE_URL = os.getenv('TICKET_SERVICE_URL', 'http://localhost:8002')

router = APIRouter()

@router.get("/nodes/{node_id}/children", response_model=List[ParkStructureTreeNode])
async def get_node_children(node_id: str, db=Depends(get_db)):
    children = await db.structure_nodes.find(
        {"parent_id": ObjectId(node_id)}
    ).to_list(None)
    return children

@router.get("/ticket-types/{ticket_type_id}/facilities", response_model=TicketTypeAccess)
async def get_ticket_type_facilities(ticket_type_id: str, db=Depends(get_db)):
    access = await db.ticket_access.find_one({"ticket_type_id": ObjectId(ticket_type_id)})
    if not access:
        raise HTTPException(status_code=404, detail="Ticket type access not found")
    return access

@router.get("/structure/tree")
async def get_full_structure(db=Depends(get_db)):
    nodes = await db.structure_nodes.find().to_list(None)
    tree = {}
    
    # 노드를 트리 구조로 구성
    for node in nodes:
        node_id = str(node["_id"])
        if not node["parent_id"]:
            tree[node_id] = {"node": node, "children": {}}
        else:
            parent_id = str(node["parent_id"])
            if parent_id in tree:
                tree[parent_id]["children"][node_id] = {"node": node, "children": {}}
    
    return tree 

@router.get("/access-control/{ticket_type_id}")
async def get_access_control(ticket_type_id: str, db=Depends(get_db)):
    access = await db.access_control.find_one(
        {"ticket_type_id": ObjectId(ticket_type_id)}
    )
    if not access:
        raise HTTPException(status_code=404, detail="Access control not found")
    return access

@router.post("/access-control/{ticket_type_id}")
async def update_access_control(
    ticket_type_id: str,
    park_id: str,
    facility_ids: List[str],
    db=Depends(get_db)
):
    access_data = {
        "ticket_type_id": ObjectId(ticket_type_id),
        "park_id": ObjectId(park_id),
        "facility_ids": [ObjectId(fid) for fid in facility_ids],
        "updated_at": datetime.utcnow()
    }
    
    result = await db.access_control.update_one(
        {"ticket_type_id": ObjectId(ticket_type_id)},
        {"$set": access_data},
        upsert=True
    )
    
    return {"message": "Access control updated"}

@router.post("/validate/park-update")
async def validate_park_update(park_id: str, db=Depends(get_db)):
    # 공원에 연결된 시설들 확인
    facilities = await db.structure_nodes.find(
        {"parent_id": ObjectId(park_id), "node_type": "facility"}
    ).to_list(None)
    
    # 공원에 연결된 티켓 타입 확인
    ticket_types = await db.ticket_access.find(
        {"park_id": ObjectId(park_id)}
    ).to_list(None)
    
    return {
        "can_update": True,
        "facilities_count": len(facilities),
        "ticket_types_count": len(ticket_types)
    }

@router.post("/validate/facility-update")
async def validate_facility_update(facility_id: str, db=Depends(get_db)):
    # 시설이 사용된 티켓 접근 권한 확인
    access_controls = await db.ticket_access.find(
        {"facility_ids": ObjectId(facility_id)}
    ).to_list(None)
    
    # 시설의 예약 정보 확인 (ride_reservation_service와 통신)
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{RESERVATION_SERVICE_URL}/api/reservations/facility/{facility_id}/active"
        )
        if response.status_code == 200:
            active_reservations = response.json()
        else:
            active_reservations = []
    
    return {
        "can_update": True,
        "access_controls_count": len(access_controls),
        "active_reservations_count": len(active_reservations)
    }

@router.post("/validate/ticket-type-update")
async def validate_ticket_type_update(ticket_type_id: str, db=Depends(get_db)):
    # 해당 티켓 타입으로 발급된 활성 티켓 확인
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{TICKET_SERVICE_URL}/api/tickets/active/by-type/{ticket_type_id}"
        )
        if response.status_code == 200:
            active_tickets = response.json()
        else:
            active_tickets = []
    
    return {
        "can_update": len(active_tickets) == 0,
        "active_tickets_count": len(active_tickets)
    }