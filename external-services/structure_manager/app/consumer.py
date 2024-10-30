import aio_pika
import json
import asyncio
from .database import get_db
from bson import ObjectId
from datetime import datetime

async def process_structure_update(message):
    async with message.process():
        db = await get_db()
        data = json.loads(message.body.decode())
        
        try:
            if data["action"] == "create":
                await handle_create(db, data)
            elif data["action"] == "update":
                await handle_update(db, data)
            elif data["action"] == "delete":
                await handle_delete(db, data)
            elif data["action"] == "link":
                await handle_link(db, data)
        except Exception as e:
            print(f"Error processing message: {e}")

async def handle_create(db, data):
    node_data = {
        "node_type": data["node_type"],
        "reference_id": ObjectId(data["reference_id"]),
        "name": data["name"],
        "level": 0 if data["node_type"] == "park" else 1,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    if "parent_id" in data and data["parent_id"]:
        node_data["parent_id"] = ObjectId(data["parent_id"])
        parent = await db.structure_nodes.find_one({"_id": node_data["parent_id"]})
        if parent:
            node_data["level"] = parent["level"] + 1
    
    await db.structure_nodes.insert_one(node_data)
    print(f"Created new {data['node_type']} node: {data['name']}")

async def handle_update(db, data):
    update_data = {
        "name": data["name"],
        "updated_at": datetime.utcnow()
    }
    await db.structure_nodes.update_one(
        {"reference_id": ObjectId(data["reference_id"])},
        {"$set": update_data}
    )
    print(f"Updated node: {data['reference_id']}")

async def handle_delete(db, data):
    await db.structure_nodes.delete_one(
        {"reference_id": ObjectId(data["reference_id"])}
    )
    print(f"Deleted node: {data['reference_id']}")

async def handle_link(db, data):
    await db.structure_nodes.update_one(
        {"reference_id": ObjectId(data["reference_id"])},
        {"$set": {
            "parent_id": ObjectId(data["parent_id"]),
            "updated_at": datetime.utcnow()
        }}
    )
    print(f"Linked node {data['reference_id']} to parent {data['parent_id']}")

async def start_consumer(channel):
    queue = await channel.declare_queue(
        "structure_updates",
        durable=True
    )
    
    await queue.consume(process_structure_update)
    
    try:
        await asyncio.Future()  # run forever
    finally:
        await channel.close() 