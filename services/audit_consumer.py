import boto3
import json
import time
from datetime import datetime
from collections import defaultdict

AWS_ENDPOINT = "http://localhost:4566"
REGION = "us-east-1"

QUEUE_NAME = "audit-trace-queue"

sqs = boto3.client(
    "sqs",
    region_name=REGION,
    endpoint_url=AWS_ENDPOINT,
    aws_access_key_id="test",
    aws_secret_access_key="test"
)

def get_queue_url(name):
    return sqs.get_queue_url(QueueName=name)["QueueUrl"]

queue_url = get_queue_url(QUEUE_NAME)

#memoria simple de la saga
sagas = defaultdict(list)
completed_sagas = {}

def extract_event(body):
    raw = json.loads(body)
    if "Message" in raw:
        return json.loads(raw["Message"])
    return raw


def log_timeline(correlation_id):
    events = sagas[correlation_id]

    print("\n" + "="*40)
    print(f"SAGA {correlation_id}")
    for e in events:
        print(f"- {e}")
    print("="*40)


def process_message(body):
    event = extract_event(body)

    event_type = event.get("eventType")
    correlation_id = event.get("correlationId", "UNKNOWN")

    # guardamos evento (evitar duplicados opcional)
    if event_type not in sagas[correlation_id]:
        sagas[correlation_id].append(event_type)

    print(f"[AUDIT] {event_type} | {correlation_id}")

    # imprime timeline
    log_timeline(correlation_id)

    # AQUÍ se detecta cierre de saga(aunque no este completa)
    if correlation_id not in completed_sagas or True:

        if is_ready_to_persist(sagas[correlation_id]):

            final_status = (
                "OrderCompleted"
                if "OrderCompleted" in sagas[correlation_id]
                else "OrderCancelled"
            )

            completed_sagas[correlation_id] = {
                "orderId": correlation_id,
                "finalStatus": final_status,
                "events": sagas[correlation_id],
                "completedAt": datetime.utcnow().isoformat()
            }

            flush_completed_sagas()

    return True


def is_ready_to_persist(events):

    # caso éxito → inmediato
    if "OrderCompleted" in events:
        return True

    # caso cancelado
    if "OrderCancelled" in events:
        # si hubo compensación, espera release
        if "InventoryReleaseRequested" in events:
            return "InventoryReleased" in events
        return True

    return False

def persist_completed_saga(order_id, events, final_status):
    record = {
        "orderId": order_id,
        "finalStatus": final_status,
        "events": events,
        "completedAt": datetime.utcnow().isoformat()
    }

    with open("completed_sagas.jsonl", "a") as f:
        f.write(json.dumps(record) + "\n")


def flush_completed_sagas():
    with open("completed_sagas.json", "w") as f:
        json.dump(completed_sagas, f, indent=2)


def main():
    print("[START] Audit Consumer running...")

    while True:
        response = sqs.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=5,
            WaitTimeSeconds=5
        )

        messages = response.get("Messages", [])

        for msg in messages:
            receipt = msg["ReceiptHandle"]

            try:
                process_message(msg["Body"])

                sqs.delete_message(
                    QueueUrl=queue_url,
                    ReceiptHandle=receipt
                )

            except Exception as e:
                print(f"[ERROR] {e}")

        time.sleep(1)


if __name__ == "__main__":
    main()