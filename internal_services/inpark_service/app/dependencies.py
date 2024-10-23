from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from .database import redis_client

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    guest_keys = await redis_client.keys("guest:*")
    for key in guest_keys:
        guest_info = await redis_client.hgetall(key)
        if guest_info.get("token") == token:
            return {"id": key.split(":")[1], **guest_info}
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
