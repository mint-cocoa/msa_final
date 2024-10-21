from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import httpx
import os

app = FastAPI()

# 환경 변수에서 서비스 URL 가져오기
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:8000")
PARK_SERVICE_URL = os.getenv("PARK_SERVICE_URL", "http://park-service:8000")
FACILITY_SERVICE_URL = os.getenv("FACILITY_SERVICE_URL", "http://facility-service:8000")
TICKET_SERVICE_URL = os.getenv("TICKET_SERVICE_URL", "http://ticket-service:8000")
INPARK_SERVICE_URL = os.getenv("INPARK_SERVICE_URL", "http://inpark-service:8000")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Theme Park API Gateway"}

async def proxy_request(url: str, method: str, path: str, json: dict = None, params: dict = None):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(method, f"{url}{path}", json=json, params=params)
            return JSONResponse(content=response.json(), status_code=response.status_code)
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Service unavailable: {exc}")

@app.get("/users/{path:path}")
async def proxy_users(path: str):
    return await proxy_request(USER_SERVICE_URL, "GET", f"/users/{path}")

@app.get("/parks/{path:path}")
async def proxy_parks(path: str):
    return await proxy_request(PARK_SERVICE_URL, "GET", f"/parks/{path}")

@app.get("/facilities/{path:path}")
async def proxy_facilities(path: str):
    return await proxy_request(FACILITY_SERVICE_URL, "GET", f"/facilities/{path}")

@app.get("/tickets/{path:path}")
async def proxy_tickets(path: str):
    return await proxy_request(TICKET_SERVICE_URL, "GET", f"/tickets/{path}")

@app.post("/tickets/{path:path}")
async def proxy_create_ticket(path: str, ticket_data: dict):
    return await proxy_request(TICKET_SERVICE_URL, "POST", f"/tickets/{path}", json=ticket_data)

@app.get("/inpark/{path:path}")
async def proxy_inpark(path: str):
    return await proxy_request(INPARK_SERVICE_URL, "GET", f"/inpark/{path}")

@app.post("/inpark/{path:path}")
async def proxy_inpark_action(path: str, action_data: dict):
    return await proxy_request(INPARK_SERVICE_URL, "POST", f"/inpark/{path}", json=action_data)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
