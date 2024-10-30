FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV MONGODB_URI="mongodb://root:example@mongodb:27017/structure?authSource=admin"
ENV DATABASE_NAME="structure"
ENV RABBITMQ_URL="amqp://guest:guest@rabbitmq:5672/"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 