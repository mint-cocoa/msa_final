import aio_pika
import json
import asyncio
from .database import get_db
from bson import ObjectId
from datetime import datetime
import httpx

class StructureConsumer:
    def __init__(self, connection: aio_pika.Connection):
        self.connection = connection
        self.channel = None
        self.db = None

    async def setup(self):
        self.channel = await self.connection.channel()
        self.db = await get_db()
        
        # 각각의 큐 선언
        await self.channel.declare_queue('structure_updates', durable=True)
        await self.channel.declare_queue('park_events', durable=True)
        await self.channel.declare_queue('facility_events', durable=True)
        await self.channel.declare_queue('ticket_events', durable=True)

    async def start_consuming(self):
        # 각 큐에 대한 consumer 설정
        structure_queue = await self.channel.declare_queue('structure_updates', durable=True)
        park_queue = await self.channel.declare_queue('park_events', durable=True)
        facility_queue = await self.channel.declare_queue('facility_events', durable=True)
        ticket_queue = await self.channel.declare_queue('ticket_events', durable=True)

        await structure_queue.consume(self.process_structure_update)
        await park_queue.consume(self.process_park_event)
        await facility_queue.consume(self.process_facility_event)
        await ticket_queue.consume(self.process_ticket_event)

    async def process_structure_update(self, message: aio_pika.IncomingMessage):
        async with message.process():
            data = json.loads(message.body.decode())
            try:
                if data["action"] == "create":
                    await self.handle_create(data)
                elif data["action"] == "update":
                    await self.handle_update(data)
                elif data["action"] == "delete":
                    await self.handle_delete(data)
                elif data["action"] == "link":
                    await self.handle_link(data)
            except Exception as e:
                print(f"Error processing structure update: {e}")

    async def process_park_event(self, message: aio_pika.IncomingMessage):
        async with message.process():
            data = json.loads(message.body.decode())
            try:
                result = await self.handle_park_event(data)
                # 결과를 응답 큐로 전송
                await self.publish_response('park_responses', {
                    'request_id': data.get('request_id'),
                    'result': result
                })
            except Exception as e:
                print(f"Error processing park event: {e}")

    async def process_facility_event(self, message: aio_pika.IncomingMessage):
        async with message.process():
            data = json.loads(message.body.decode())
            try:
                result = await self.handle_facility_event(data)
                await self.publish_response('facility_responses', {
                    'request_id': data.get('request_id'),
                    'result': result
                })
            except Exception as e:
                print(f"Error processing facility event: {e}")

    async def process_ticket_event(self, message: aio_pika.IncomingMessage):
        async with message.process():
            data = json.loads(message.body.decode())
            try:
                result = await self.handle_ticket_event(data)
                await self.publish_response('ticket_responses', {
                    'request_id': data.get('request_id'),
                    'result': result
                })
            except Exception as e:
                print(f"Error processing ticket event: {e}")

    async def handle_park_event(self, data: dict):
        if data["action"] == "validate_update":
            park_id = data["park_id"]
            facilities = await self.db.structure_nodes.find(
                {"parent_id": ObjectId(park_id), "node_type": "facility"}
            ).to_list(None)
            
            ticket_types = await self.db.ticket_access.find(
                {"park_id": ObjectId(park_id)}
            ).to_list(None)
            
            return {
                "can_update": True,
                "facilities_count": len(facilities),
                "ticket_types_count": len(ticket_types)
            }
        return {"error": "Unknown action"}

    async def handle_facility_event(self, data: dict):
        if data["action"] == "validate_update":
            facility_id = data["facility_id"]
            access_controls = await self.db.ticket_access.find(
                {"facility_ids": ObjectId(facility_id)}
            ).to_list(None)
            
            return {
                "can_update": True,
                "access_controls_count": len(access_controls)
            }
        return {"error": "Unknown action"}

    async def handle_ticket_event(self, data: dict):
        if data["action"] == "validate_update":
            ticket_type_id = data["ticket_type_id"]
            access = await self.db.access_control.find_one(
                {"ticket_type_id": ObjectId(ticket_type_id)}
            )
            return {
                "can_update": access is not None,
                "access_exists": access is not None
            }
        return {"error": "Unknown action"}

    async def publish_response(self, queue_name: str, response: dict):
        await self.channel.default_exchange.publish(
            aio_pika.Message(body=json.dumps(response).encode()),
            routing_key=queue_name
        )

    async def close(self):
        if self.channel:
            await self.channel.close() 