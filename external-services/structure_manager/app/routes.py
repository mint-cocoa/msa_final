from fastapi import APIRouter, HTTPException, Depends, Request
from .models import ParkStructureTreeNode, TicketTypeAccess, NodeCreate
from .database import get_db
from bson import ObjectId
from typing import List
import asyncio

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