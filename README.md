# RabbitHunter

Run until a RabbitMQ queue is drained. If the queue is empty when service launches, it will run until the queue has had messages added, and then returns to 0 messages.

This can be used as an container in an AWS ECS task, set as an essential task, so that when it exists, the task will exit.

# Configuration

All configuration is through environment variables.

## Required

- `rabbitmq_management_host` - RabbitMQ host, format is `hostname:port`
- `rabbitmq_management_user` - RabbitMQ username
- `rabbitmq_management_password` - RabbitMQ password

## Optional

- `rabbitmq_vhost` - RabbitMQ vhost, default is `/`
- `SLEEP_INTERVAL` - Number of seconds between polling rabbitMQ. Default is `15`.
- `TIMEOUT` - Automatically terminate if queue is not drained after `TIMEOUT` seconds. Default is 172800, which is 2 days.
- `DEBUG` - enable more logging. This will log message count after each sleep interval.
