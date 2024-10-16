from .models import ParkCreate, ParkRead, TicketTypeCreate
from pymongo import MongoClient
from datetime import datetime

client = MongoClient('mongodb://localhost:27017/')
db = client['park_database']
parks_collection = db['parks']
tickets_collection = db['tickets']

def create_park_with_tickets(park: ParkCreate) -> ParkRead:
    park_dict = park.dict(by_alias=True)
    park_dict['created_at'] = datetime.utcnow()
    park_dict['updated_at'] = datetime.utcnow()
    
    # 파크 저장
    result = parks_collection.insert_one(park_dict)
    park_id = result.inserted_id
    
    # 티켓 저장
    for ticket in park.ticket_types:
        ticket_dict = ticket.dict(by_alias=True)
        ticket_dict['park_id'] = str(park_id)
        ticket_dict['created_at'] = datetime.utcnow()
        ticket_dict['updated_at'] = datetime.utcnow()
        tickets_collection.insert_one(ticket_dict)
    
    # 저장된 파크 반환
    created_park = parks_collection.find_one({"_id": park_id})
    return ParkRead(**created_park, by_alias=True)
