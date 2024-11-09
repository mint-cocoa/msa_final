from fastapi import APIRouter, HTTPException, Request, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging
from .database import get_db

router = APIRouter()

@router.get("/structure/all")
async def get_all_structure(db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        # nodes 컬렉션에서 모든 구조 정보 조회
        nodes = await db.nodes.find({}).to_list(None)
        
        # ObjectId를 문자열로 변환
        for node in nodes:
            node['_id'] = str(node['_id'])
            if 'reference_id' in node:
                node['reference_id'] = str(node['reference_id'])
            if 'facilities' in node:
                node['facilities'] = [str(f) for f in node['facilities']]
        
        return {
            "status": "success",
            "data": nodes
        }
        
    except Exception as e:
        logging.error(f"Failed to get structure: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to retrieve structure: {str(e)}"
        )
    
@router.get("/health")
async def health():
    return {"status": "ok"}
    