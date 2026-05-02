import boto3
import json
import time
import random
import os
import uuid
from datetime import datetime

# Config
AWS_ENDPOINT = "http://localhost:4566"
REGION = "us-east-1"

QUEUE_NAME = "inventory-queue"
TOPIC_NAME = "inventory-events"

# Cliente SQS
sqs = boto3.client(
    "sqs",
    region_name=REGION,
    endpoint_url=AWS_ENDPOINT,
    aws_access_key_id="test",
    aws_secret_access_key="test"
)

# Cliente SNS
sns = boto3.client(
    "sns",
    region_name=REGION,
    endpoint_url=AWS_ENDPOINT,
    aws_access_key_id="test",
    aws_secret_access_key="test"
)

# Obtener Queue URL dinámicamente
def get_queue_url(queue_name):
    response = sqs.get_queue_url(QueueName=queue_name)
    return response["QueueUrl"]

# Obtener Topic ARN dinámicamente
def get_topic_arn(topic_name):
    topics = sns.list_topics()["Topics"]
    for t in topics:
        if topic_name in t["TopicArn"]:
            return t["TopicArn"]
    raise Exception(f"Topic {topic_name} not found")

queue_url = get_queue_url(QUEUE_NAME)
topic_arn = get_topic_arn(TOPIC_NAME)

print(f"[INIT] Queue URL: {queue_url}")
print(f"[INIT] Topic ARN: {topic_arn}")

# Publicar evento a SNS
def publish_event(event, original_event):
    
    enriched_event = {
        "eventId": str(uuid.uuid4()),
        "eventType": event.get("eventType"),
        "timestamp": datetime.utcnow().isoformat(),
        "source": "inventory-consumer",  # cambia según el consumer
        "orderId": event.get("orderId"),
        "correlationId": original_event.get("correlationId")
    }
    
    # opcional: mergear payload si viene
    if "payload" in event:
        enriched_event["payload"] = event["payload"]

    print(f"[PUBLISH] {enriched_event['eventType']} | {enriched_event['orderId']}")
    
    sns.publish(
        TopicArn=topic_arn,
        Message=json.dumps(enriched_event)
    )

def extract_event(body):
    raw = json.loads(body)

    if "Message" in raw:
        print("[DEBUG] SNS message detected")
        return json.loads(raw["Message"])

    print("[DEBUG] Direct message")
    return raw

def process_message(body):
    try:
        event = extract_event(body)
        event_type = event.get("eventType")

        print(f"[PROCESS] EventType: {event_type}")

        # Validación básica
        if not event_type:
            print(f"[WARN] Missing eventType in event: {event}")
            return False

        # --- OrderCreated ---
        if event_type == "OrderCreated":
            order_id = event.get("orderId")

            if random.random() < 0.7:
                # SUCCESS
                new_event = {
                    "eventType": "InventorySuccess",
                    "orderId": order_id
                }
            else:
                # FAIL
                new_event = {
                    "eventType": "InventoryFailed",
                    "orderId": order_id
                }

            publish_event(new_event,event)
            return True

        # --- Compensation ---
        elif event_type == "InventoryReleaseRequested":
            order_id = event.get("orderId")

            new_event = {
                "eventType": "InventoryReleased",
                "orderId": order_id
            }

            publish_event(new_event, event)
            return True

        else:
            print(f"[SKIP] Event not handled: {event_type}")
            return True  # importante: no es error, solo no aplica

    except Exception as e:
        print(f"[ERROR] Processing failed: {str(e)}")
        return False

# Loop principal
def main():
    print("[START] Inventory Consumer running...")

    while True:
        response = sqs.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=5,
            WaitTimeSeconds=5
        )

        messages = response.get("Messages", [])

        if not messages:
            continue

        for msg in messages:
            receipt_handle = msg["ReceiptHandle"]
            body = msg["Body"]

            #print("\n[RAW MESSAGE]", body)

            success = process_message(body)

            if success:
                sqs.delete_message(
                    QueueUrl=queue_url,
                    ReceiptHandle=receipt_handle
                )
                print("[DELETE] Message processed and removed")
            else:
                print("[RETRY] Message will be retried")

        time.sleep(1)


if __name__ == "__main__":
    main()