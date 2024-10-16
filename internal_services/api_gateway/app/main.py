from fastapi import FastAPI, HTTPException
import httpx

app = FastAPI()

RIDE_RESERVATION_SERVICE_URL = "http://ride_reservation_service:8000"
NOTIFICATION_SERVICE_URL = "http://notification_service:8000"
REAL_TIME_TRACKING_SERVICE_URL = "http://real_time_tracking_service:8000"

@app.post("/reserve-ride/{ride_id}")
async def reserve_ride(ride_id: str, user_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{RIDE_RESERVATION_SERVICE_URL}/reserve/{ride_id}?user_id={user_id}")
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.json())
    return response.json()

@app.get("/notifications")
async def get_notifications():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{NOTIFICATION_SERVICE_URL}/")
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.json())
    return response.json()

@app.get("/real-time-tracking")
async def get_real_time_tracking():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{REAL_TIME_TRACKING_SERVICE_URL}/")
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.json())
    return response.json()

# 기존의 다른 라우트들...

