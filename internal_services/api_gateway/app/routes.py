# routers/tickets.py
from fastapi import APIRouter, HTTPException, status
from database import ticket_collection, redis_client
from models import UseTicketResponse
from bson.objectid import ObjectId

router = APIRouter()

@router.post("/use_ticket/{token}", response_model=UseTicketResponse, responses={404: {"model": dict}})
async def use_ticket_endpoint(token: str):
    # Find the ticket in MongoDB
    ticket = await ticket_collection.find_one({"token": token})
    
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="티켓을 찾을 수 없습니다.")
    
    # Optionally, check if the ticket is already used
    if ticket.get("used"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="이미 사용된 티켓입니다.")
    
    # Mark the ticket as used instead of deleting (optional)
    await ticket_collection.update_one({"token": token}, {"$set": {"used": True}})
    
    # Manage guest in Redis
    guest_id = str(ticket.get("_id"))  # Or any unique identifier for the guest
    guest_info = {
        "token": token,
        "used_at": ticket.get("used_at") or "current_timestamp",  # Replace with actual timestamp
        # Add more fields as necessary
    }
    
    # Add guest to a Redis set or hash. Here, using a Redis hash with guest_id as key
    await redis_client.hset(f"guest:{guest_id}", mapping=guest_info)
    
    # Optionally, add to a sorted set with a timestamp for ordering or expiration
    # await redis_client.zadd("active_guests", {guest_id: timestamp})
    
    # Optionally, set an expiration for guest data in Redis
    # await redis_client.expire(f"guest:{guest_id}", 3600)  # Expires in 1 hour
    
    # Get current guest count
    guest_keys = await redis_client.keys("guest:*")
    guest_count = len(guest_keys)
    
    return UseTicketResponse(message="티켓이 사용되었습니다.", guest_count=guest_count)
