from fastapi import APIRouter, HTTPException, Depends
from .models import TreeNode, NodeCreate
from .database import get_db
from bson import ObjectId
from typing import List
import asyncio

router = APIRouter()


@router.get("/nodes/{node_id}/subtree", response_model=TreeNode)
async def get_node_subtree(node_id: str, db=Depends(get_db)):
    # 현재 노드 조회
    node = await db.structure_nodes.find_one({"_id": ObjectId(node_id)})
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    
    # 직계 자식 노드들만 조회
    children = await db.structure_nodes.find({
        "parent_id": ObjectId(node_id)
    }).to_list(None)
    
    # 현재 노드에 자식 노드들 추가
    node['children'] = children
    return node

@router.post("/nodes", response_model=TreeNode)
async def create_node(node: NodeCreate, db=Depends(get_db)):
    # 부모 노드 레벨 확인 및 새 노드 레벨 설정
    ancestors = []
    level = 0
    
    if node.parent_id:
        parent = await db.structure_nodes.find_one({"_id": ObjectId(node.parent_id)})
        if not parent:
            raise HTTPException(status_code=404, detail="Parent node not found")
        level = parent["level"] + 1
        ancestors = parent.get("ancestors", []) + [ObjectId(node.parent_id)]

    node_data = {
        "parent_id": ObjectId(node.parent_id) if node.parent_id else None,
        "node_type": node.node_type,
        "reference_id": ObjectId(node.reference_id),
        "name": node.name,
        "level": level,
        "ancestors": ancestors,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await db.structure_nodes.insert_one(node_data)
    created_node = await db.structure_nodes.find_one({"_id": result.inserted_id})
    return TreeNode(**created_node, children=[])
