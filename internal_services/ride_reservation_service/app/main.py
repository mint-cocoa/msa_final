from fastapi import FastAPI, HTTPException
from kafka import KafkaProducer, KafkaConsumer
import json

app = FastAPI()

producer = KafkaProducer(bootstrap_servers=['kafka:9092'],
                         value_serializer=lambda v: json.dumps(v).encode('utf-8'))

@app.post("/reserve/{ride_id}")
async def reserve_ride(ride_id: str, user_id: str):
    # 여기서 실제 예약 로직을 구현합니다
    reservation = {"ride_id": ride_id, "user_id": user_id}
    producer.send('ride_reservations', reservation)
    return {"message": "예약이 완료되었습니다."}

# Kafka 컨슈머 로직 (별도의 스레드에서 실행)
def consume_messages():
    consumer = KafkaConsumer('ride_status',
                             bootstrap_servers=['kafka:9092'],
                             value_deserializer=lambda x: json.loads(x.decode('utf-8')))
    for message in consumer:
        # 여기서 메시지를 처리합니다 (예: 데이터베이스 업데이트)
        print(message.value)

import threading
threading.Thread(target=consume_messages, daemon=True).start()
