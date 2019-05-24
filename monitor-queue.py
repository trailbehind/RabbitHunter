#!/usr/bin/env python3
import os
from time import sleep
import sys
import logging
import boto3
from pyrabbit.api import Client


def get_queue_depths(host, username, password, vhost):
    cl = Client(host, username, password)
    if not cl.is_alive():
        raise Exception("Failed to connect to rabbitmq")
    depths = {}
    queues = [q["name"] for q in cl.get_queues(vhost=vhost)]
    for queue in queues:
        if queue == "aliveness-test":
            continue
        depths[queue] = cl.get_queue_depth(vhost, queue)
    return depths


def terminate(success):
    cluster_name = os.environ.get("ECS_CLUSTER")
    task_definition_name = os.environ.get("TASK_DEFINITION_NAME")
    # TODO: find ARN of current task
    # TODO: kill task
    sys.exit(0)


if __name__ == "__main__":
    sleep_interval = int(os.environ.get("SLEEP_INTERVAL", 15)) # check often in case things finish quickly
    timeout = int(os.environ.get("TIMEOUT", 60*60*24*2))
    queue_had_messages = False
    elapsed = 0
    while True:
        depths = get_queue_depths(
            os.environ.get("rabbitmq_management_host"),
            os.environ.get("rabbitmq_management_user"),
            os.environ.get("rabbitmq_management_password"),
            os.environ.get("rabbitmq_vhost", "/")
        )
        message_count = sum(depths.values())
        if queue_had_messages == False and message_count > 0:
            logging.info("Found messages in queue")
            queue_had_messages = True
        elif queue_had_messages and message_count == 0:
            logging.info("Queue has drained, terminating")
            terminate(True)
        elif elapsed > timeout:
            logging.info("Timeout exceeded, terminating")
            terminate(False)
        else:
            logging.debug("Sleeping")
            sleep(sleep_interval)
            elapsed += sleep_interval
