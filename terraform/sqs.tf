############################################
# MAIN QUEUES
############################################

resource "aws_sqs_queue" "order_queue" {
  name = "order-queue"

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.order_dlq.arn
    maxReceiveCount     = 3
  })
}

resource "aws_sqs_queue" "inventory_queue" {
  name = "inventory-queue"

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.inventory_dlq.arn
    maxReceiveCount     = 3
  })
}

resource "aws_sqs_queue" "payment_queue" {
  name = "payment-queue"

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.payment_dlq.arn
    maxReceiveCount     = 3
  })
}


resource "aws_sqs_queue" "audit_trace_queue" {
  name = "audit-trace-queue"
}




