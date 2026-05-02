resource "aws_sqs_queue" "order_dlq" {
  name = "order-dlq"
}

resource "aws_sqs_queue" "inventory_dlq" {
  name = "inventory-dlq"
}

resource "aws_sqs_queue" "payment_dlq" {
  name = "payment-dlq"
}

