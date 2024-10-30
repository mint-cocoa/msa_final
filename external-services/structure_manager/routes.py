from fastapi import APIRouter, HTTPException, Depends
from .models import ParkStructureTreeNode, TicketTypeAccess, NodeCreate
from .database import get_db
from bson import ObjectId
from typing import List
import asyncio

router = APIRouter()

@router.post("/nodes", response_model=ParkStructureTreeNode)
async def create_node(node: NodeCreate, db=Depends(get_db)):
    # 부모 노드 레벨 확인 및 새 노드 레벨 설정
    level = 0
    if node.parent_id:
        parent = await db.structure_nodes.find_one({"_id": ObjectId(node.parent_id)})
        if not parent:
            raise HTTPException(status_code=404, detail="Parent node not found")
        level = parent["level"] + 1

    node_data = {
        "parent_id": ObjectId(node.parent_id) if node.parent_id else None,
        "node_type": node.node_type,
        "reference_id": ObjectId(node.reference_id),
        "name": node.name,
        "level": level
    }
    
    result = await db.structure_nodes.insert_one(node_data)
    created_node = await db.structure_nodes.find_one({"_id": result.inserted_id})
    return created_node

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

@router.post("/ticket-types/{ticket_type_id}/facilities")
async def update_ticket_type_facilities(
    ticket_type_id: str,
    facility_ids: List[str],
    db=Depends(get_db)
):
    facility_object_ids = [ObjectId(fid) for fid in facility_ids]
    result = await db.ticket_access.update_one(
        {"ticket_type_id": ObjectId(ticket_type_id)},
        {
            "$set": {
                "facility_ids": facility_object_ids,
                "updated_at": datetime.utcnow()
            }
        },
        upsert=True
    )
    return {"message": "Ticket type facilities updated"}

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