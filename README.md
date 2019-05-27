# Tiler-Killer

Service to stop an ECS task when a RabbitMQ queue is drained. If the queue is empty when service launches, no action will be taken until the queue has had messages added, and then returns to 0 messages.

# Configuration

All configuration is through environment variables.

## Required

- `rabbitmq_management_host` - RabbitMQ host, format is `hostname:port`
- `rabbitmq_management_user` - RabbitMQ username
- `rabbitmq_management_password` - RabbitMQ password
- `ECS_CLUSTER` - ECS Cluster to query for running tasks
- `TASK_DEFINITION_NAME` - ECS tasks definition to kill. Can be in the format `name:revision` or `name`.

## Optional

- `rabbitmq_vhost` - RabbitMQ vhost, default is `/`
- `AWS_REGION` - AWS region to use, default is `us-east-1`
- `SLEEP_INTERVAL` - Number of seconds between polling rabbitMQ. Default is `15`.
- `TIMEOUT` - Automatically terminate if queue is not drained after `TIMEOUT` seconds. Default is 172800, which is 2 days.
