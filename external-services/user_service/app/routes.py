# user_service/app/routes.py
from fastapi import APIRouter, HTTPException, Depends, Request
from . import utils, models
from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm
from .database import get_db
import os
from bson import ObjectId

router = APIRouter()

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

@router.post("/", response_model=models.UserRead)
async def create_user(user: models.UserCreate, request: Request, db=Depends(get_db)):
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = utils.encrypt_password(user.password)
    user_data = user.model_dump(by_alias=True, exclude=["id"])
    user_data["password"] = hashed_password
    
    new_user = await db.users.insert_one(user_data)      
    created_user = await db.users.find_one({"_id": new_user.inserted_id})
    
    # 구조 업데이트 메시지 발행
    await publish_structure_update(
        request.app.state.rabbitmq_channel,
        {
            "action": "create",
            "node_type": "user",
            "reference_id": str(new_user.inserted_id),
            "name": user.email
        }
    )
    
    return created_user

@router.get("/{user_id}", response_model=models.UserRead)
async def get_user(user_id: str, db=Depends(get_db)):
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/login")
async def login_for_access_token(db=Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = await db.users.find_one({"email": form_data.username})
    if not user:
        raise HTTPException(
            status_code=400,
            detail="사용자 이름이나 비밀번호가 올바르지 않습니다.",
        )
    if not utils.verify_password(form_data.password, user.get("password")):
        raise HTTPException(
            status_code=400,
            detail="사용자 이름이나 비밀번호가 올바르지 않습니다.",
        )
    
    # JWT 토큰 생성
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = utils.create_access_token(
        data={
            "email": user["email"],
            "is_admin": user.get("is_admin", False)
        },
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}



