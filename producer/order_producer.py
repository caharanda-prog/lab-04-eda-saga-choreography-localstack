import json
import uuid
import random
import time
from datetime import datetime

import boto3

# Config LocalStack
sns = boto3.client(
    "sns",
    endpoint_url="http://localhost:4566",
    region_name="us-east-1",
    aws_access_key_id="test",
    aws_secret_access_key="test"
)

TOPIC_NAME = "order-events"


def get_topic_arn(topic_name):
    paginator = sns.get_paginator("list_topics")

    for page in paginator.paginate():
        for topic in page["Topics"]:
            arn = topic["TopicArn"]
            if arn.endswith(f":{topic_name}"):
                return arn

    raise Exception(f"Topic {topic_name} not found")


def generate_order():
    order_id = f"ORD-{random.randint(1000, 9999)}"

    items = []
    for _ in range(random.randint(1, 3)):
        items.append({
            "productId": f"P-{random.randint(1, 10)}",
            "quantity": random.randint(1, 5)
        })

    event = {
        "eventId": str(uuid.uuid4()),
        "eventType": "OrderCreated",
        "timestamp": datetime.utcnow().isoformat(),
        "source": "order-producer",
        "orderId": order_id,
        "correlationId": order_id,
        "payload": {
            "customerId": f"CUST-{random.randint(1, 50)}",
            "amount": round(random.uniform(50, 500), 2),
            "items": items
        }
    }

    return event


def publish_event(topic_arn, event):
    sns.publish(
        TopicArn=topic_arn,
        Message=json.dumps(event)
    )

    print(f"Published {event['eventType']} for {event['orderId']}")


def main():
    topic_arn = get_topic_arn(TOPIC_NAME)
    print(f"Using topic: {topic_arn}\n")

    total_orders = random.randint(10, 15)
    print(f"Generating {total_orders} orders...\n")

    for _ in range(total_orders):
        event = generate_order()
        publish_event(topic_arn, event)
        time.sleep(random.uniform(0.5, 1.5))


if __name__ == "__main__":
    main()