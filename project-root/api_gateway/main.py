from fastapi import FastAPI, HTTPException
import httpx

app = FastAPI()

USER_SERVICE_URL = "http://user_service:8000"
PARK_SERVICE_URL = "http://park_service:8000"
FACILITY_SERVICE_URL = "http://facility_service:8000"
RIDE_RESERVATION_SERVICE_URL = "http://ride_reservation_service:8000"
NOTIFICATION_SERVICE_URL = "http://notification_service:8000"
REAL_TIME_TRACKING_SERVICE_URL = "http://real_time_tracking_service:8000"
TICKET_SERVICE_URL = "http://ticket_service:8000"

@app.get("/")
def read_root():
    return {"message": "Welcome to the Theme Park API Gateway"}

# 기존 라우트들...

@app.post("/ride-reservations/")
async def proxy_ride_reservations():
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{RIDE_RESERVATION_SERVICE_URL}/reserve")
        return response.json()

@app.get("/notifications/")
async def proxy_notifications():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{NOTIFICATION_SERVICE_URL}/")
        return response.json()

@app.get("/real-time-tracking/")
async def proxy_real_time_tracking():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{REAL_TIME_TRACKING_SERVICE_URL}/")
        return response.json()

@app.post("/enter-park/{token}")
async def enter_park(token: str):
    async with httpx.AsyncClient() as client:
        # 티켓 검증
        validate_response = await client.get(f"{TICKET_SERVICE_URL}/validate/{token}")
        if validate_response.status_code != 200:
            raise HTTPException(status_code=validate_response.status_code, detail="Invalid ticket")
        
        # 티켓 사용 처리 및 JWT 토큰 발급
        use_response = await client.post(f"{TICKET_SERVICE_URL}/use/{token}")
        if use_response.status_code != 200:
            raise HTTPException(status_code=use_response.status_code, detail="Failed to use ticket")
        
        return use_response.json()
