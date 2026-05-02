############################################
# SNS TOPICS
############################################
resource "aws_sns_topic" "order_events" {
  name = "order-events"
}

resource "aws_sns_topic" "inventory_events" {
  name = "inventory-events"
}

resource "aws_sns_topic" "payment_events" {
  name = "payment-events"
}

