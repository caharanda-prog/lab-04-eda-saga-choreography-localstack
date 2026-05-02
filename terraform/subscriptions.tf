############################################
# SNS -> SQS SUBSCRIPTIONS
############################################

resource "aws_sns_topic_subscription" "order_to_inventory" {
  topic_arn = aws_sns_topic.order_events.arn
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.inventory_queue.arn
}

resource "aws_sns_topic_subscription" "inventory_to_order" {
  topic_arn = aws_sns_topic.inventory_events.arn
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.order_queue.arn
}

resource "aws_sns_topic_subscription" "inventory_to_inventory" {
  topic_arn = aws_sns_topic.inventory_events.arn
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.inventory_queue.arn
}

resource "aws_sns_topic_subscription" "payment_to_order" {
  topic_arn = aws_sns_topic.payment_events.arn
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.order_queue.arn
}

resource "aws_sns_topic_subscription" "inventory_to_payment" {
  topic_arn = aws_sns_topic.inventory_events.arn
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.payment_queue.arn
}

resource "aws_sns_topic_subscription" "payment_to_inventory" {
  topic_arn = aws_sns_topic.payment_events.arn
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.inventory_queue.arn
}

resource "aws_sns_topic_subscription" "order_to_audit" {
  topic_arn = aws_sns_topic.order_events.arn
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.audit_trace_queue.arn
}

resource "aws_sns_topic_subscription" "inventory_to_audit" {
  topic_arn = aws_sns_topic.inventory_events.arn
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.audit_trace_queue.arn
}

resource "aws_sns_topic_subscription" "payment_to_audit" {
  topic_arn = aws_sns_topic.payment_events.arn
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.audit_trace_queue.arn
}







