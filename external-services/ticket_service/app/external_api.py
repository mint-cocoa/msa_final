import os
from httpx import AsyncClient
from fastapi import HTTPException


NAMESPACE = os.getenv("NAMESPACE", "default")
USER_SERVICE_URL = f"http://user-service.{NAMESPACE}.svc.cluster.local:8000/users/api"
PARK_SERVICE_URL = f"http://park-service.{NAMESPACE}.svc.cluster.local:8000/parks/api"


async def get_user_info(user_id: str) -> dict:
    async with AsyncClient() as client:
        try:
            response = await client.get(
                f"{USER_SERVICE_URL}/{user_id}",
                timeout=5.0  # 타임아웃 설정
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise HTTPException(
                status_code=503, 
                detail="User service is unavailable"
            )

async def get_park_info(park_id: str) -> dict:
    async with AsyncClient() as client:
        try:
            response = await client.get(
                f"{PARK_SERVICE_URL}/{park_id}",
                timeout=5.0
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise HTTPException(
                status_code=503, 
                detail="Park service is unavailable"
            )