import boto3
import json
import time
import random
import uuid
from datetime import datetime

AWS_ENDPOINT = "http://localhost:4566"
REGION = "us-east-1"

QUEUE_NAME = "payment-queue"
TOPIC_NAME = "payment-events"
INVENTORY_TOPIC_NAME = "inventory-events"

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
    raise Exception(f"Topic {name} not found")

queue_url = get_queue_url(QUEUE_NAME)
payment_topic_arn = get_topic_arn(TOPIC_NAME)
inventory_topic_arn = get_topic_arn(INVENTORY_TOPIC_NAME)


def extract_event(body):
    raw = json.loads(body)
    if "Message" in raw:
        return json.loads(raw["Message"])
    return raw


def publish_event(topic_arn, event, original_event):
    
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
        TopicArn=topic_arn,
        Message=json.dumps(enriched_event)
    )


def process_message(body):
    try:
        event = extract_event(body)
        event_type = event.get("eventType")
        order_id = event.get("orderId")

        print(f"[PROCESS] EventType: {event_type} | OrderId: {order_id}")

        if not event_type:
            return False

        # --- InventorySuccess ---
        if event_type == "InventorySuccess":

            if random.random() < 0.8:
                new_event = {
                    "eventType": "PaymentSuccess",
                    "orderId": order_id
                }

                publish_event(payment_topic_arn, new_event, event)

            else:
                # falla pago
                failed_event = {
                    "eventType": "PaymentFailed",
                    "orderId": order_id
                }

                publish_event(payment_topic_arn, failed_event,event)

                # compensación
                compensation_event = {
                    "eventType": "InventoryReleaseRequested",
                    "orderId": order_id
                }

                publish_event(inventory_topic_arn, compensation_event,event)

            return True

        else:
            print(f"[SKIP] Event not handled: {event_type}")
            return True

    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return False


def main():
    print("[START] Payment Consumer running...")

    while True:
        response = sqs.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=5,
            WaitTimeSeconds=5
        )

        messages = response.get("Messages", [])

        for msg in messages:
            receipt_handle = msg["ReceiptHandle"]
            body = msg["Body"]

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