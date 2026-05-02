import boto3
import json
import time
import uuid
from datetime import datetime

AWS_ENDPOINT = "http://localhost:4566"
REGION = "us-east-1"

QUEUE_NAME = "order-queue"
TOPIC_NAME = "order-events"

sqs = boto3.client(
    "sqs",
    region_name=REGION,
    endpoint_url=AWS_ENDPOINT,
    aws_access_key_id="test",
    aws_secret_access_key="test"
)

sns = boto3.client(
    "sns",
    region_name=REGION,
    endpoint_url=AWS_ENDPOINT,
    aws_access_key_id="test",
    aws_secret_access_key="test"
)

def get_queue_url(name):
    return sqs.get_queue_url(QueueName=name)["QueueUrl"]

def get_topic_arn(name):
    topics = sns.list_topics()["Topics"]
    for t in topics:
        if name in t["TopicArn"]:
            return t["TopicArn"]
    raise Exception("Topic not found")


queue_url = get_queue_url(QUEUE_NAME)
orders_topic_arn = get_topic_arn(TOPIC_NAME)


def extract_event(body):
    raw = json.loads(body)
    if "Message" in raw:
        return json.loads(raw["Message"])
    return raw


def publish_event(event, original_event):
    
    enriched_event = {
    "eventId": str(uuid.uuid4()),
    "eventType": event.get("eventType"),
    "timestamp": datetime.utcnow().isoformat(),
    "source": "payment-consumer",  # cambia según el consumer
    "orderId": event.get("orderId"),
    "correlationId": original_event.get("correlationId")
    }
    
    # opcional: mergear payload si viene
    if "payload" in event:
        enriched_event["payload"] = event["payload"]

    print(f"[PUBLISH] {enriched_event['eventType']} | {enriched_event['orderId']}")
    
    sns.publish(
        TopicArn=orders_topic_arn,
        Message=json.dumps(enriched_event)
    )

def process_message(body):
    event = extract_event(body)
    event_type = event.get("eventType")
    order_id = event.get("orderId")

    print(f"[PROCESS] {event_type} | {order_id}")

    # --- Inventory Failed ---
    if event_type == "InventoryFailed":
        publish_event({
            "eventType": "OrderCancelled",
            "orderId": order_id
        },event)
        return True

    # --- Payment Failed ---
    elif event_type == "PaymentFailed":
        publish_event({
            "eventType": "OrderCancelled",
            "orderId": order_id
        },event)
        return True

    # --- Success path ---
    elif event_type == "InventorySuccess":
        # aquí no decides aún
        return True

    elif event_type == "PaymentSuccess":
        publish_event({
            "eventType": "OrderCompleted",
            "orderId": order_id
        },event)
        return True

    else:
        print(f"[SKIP] {event_type}")
        return True


def main():
    print("[START] Order Consumer running...")

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

                print("[DELETE] processed")

            except Exception as e:
                print(f"[ERROR] {e}")

        time.sleep(1)


if __name__ == "__main__":
    main()