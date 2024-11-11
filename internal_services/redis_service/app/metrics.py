from prometheus_client import Counter, Gauge, Histogram
from prometheus_fastapi_instrumentator import Instrumentator, metrics

# 큐 관련 메트릭
QUEUE_LENGTH = Gauge(
    "ride_queue_length",
    "Current number of people in queue",
    ["facility_id", "facility_name"]
)

WAITING_TIME = Gauge(
    "ride_estimated_waiting_time",
    "Estimated waiting time in minutes",
    ["facility_id", "facility_name"]
)

ACTIVE_RIDERS = Gauge(
    "ride_active_riders",
    "Number of currently active riders",
    ["facility_id", "facility_name"]
)

QUEUE_CAPACITY = Gauge(
    "ride_queue_capacity",
    "Maximum queue capacity",
    ["facility_id", "facility_name"]
)

# 운영 메트릭
RIDE_OPERATIONS = Counter(
    "ride_operations_total",
    "Total number of ride operations",
    ["facility_id", "operation_type"]
)

QUEUE_OPERATIONS = Histogram(
    "queue_operation_duration_seconds",
    "Time spent processing queue operations",
    ["facility_id", "operation_type"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0]
) 