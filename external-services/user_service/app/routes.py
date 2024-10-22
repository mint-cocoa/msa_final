# user_service/app/routes.py
from fastapi import APIRouter, HTTPException, Depends
from . import utils, models
from passlib.context import CryptContext
from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm
from .database import get_db
import os
from bson import ObjectId

router = APIRouter()

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

@router.post("/", response_model=models.UserRead)
async def create_user(user: models.UserCreate, db=Depends(get_db)):
    existing_user = await utils.get_user_by_email(db, user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = await db.users.insert_one(user.model_dump(by_alias=True, exclude=["id"]))      
    created_user = await db.users.find_one({"_id": new_user.inserted_id})
    return created_user

@router.get("/{user_id}", response_model=models.UserRead)
async def get_user(user_id: str, db=Depends(get_db)):
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/auth/login")
def login_for_access_token(db=Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = utils.get_user_by_email(db, email=form_data.username)
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
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = utils.create_access_token(
        data={"sub": str(user["_id"])}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta if expires_delta else datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
