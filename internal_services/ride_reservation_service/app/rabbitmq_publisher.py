import aio_pika
import json

async def publish_reservation_request(channel, user_id, ride_id):
    message = aio_pika.Message(
        body=json.dumps({"user_id": user_id, "ride_id": ride_id}).encode()
    )
    await channel.default_exchange.publish(
        message, routing_key='ride_reservations'
    )
    print(f"Published reservation request for user {user_id} on ride {ride_id}")
