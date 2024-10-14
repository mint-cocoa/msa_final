from fastapi import FastAPI
import httpx

app = FastAPI()

USER_SERVICE_URL = "http://user_service:8000"
PARK_SERVICE_URL = "http://park_service:8000"
FACILITY_SERVICE_URL = "http://facility_service:8000"

@app.get("/")
def read_root():
    return {"message": "Welcome to the API Gateway"}

@app.get("/users/")
def proxy_users():
    with httpx.Client() as client:
        response = client.get(f"{USER_SERVICE_URL}/users/")
        return response.json()

@app.get("/parks/")
def proxy_parks():
    with httpx.Client() as client:
        response = client.get(f"{PARK_SERVICE_URL}/parks/")
        return response.json()

@app.get("/facilities/")
def proxy_facilities():
    with httpx.Client() as client:
        response = client.get(f"{FACILITY_SERVICE_URL}/facilities/")
        return response.json()
