#!/usr/bin/env python3
import logging
import os
import sys
from time import sleep

import boto3
from pyrabbit.api import Client

ecs_client = boto3.client("ecs", region_name=os.environ.get("AWS_REGION", "us-east-1"))


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


def get_task_arn(cluster_name, task_definition_name):
    # get ARN from task definition name
    task_definition = ecs_client.describe_task_definition(
        taskDefinition=task_definition_name
    )["taskDefinition"]
    task_definition_arn = task_definition["taskDefinitionArn"]
    logging.debug("Found task definition ARN:%s" % task_definition_arn)

    # Get ARN of running task
    running_task_arns = ecs_client.list_tasks(cluster=cluster_name)["taskArns"]
    for task_arn in running_task_arns:
        response = ecs_client.describe_tasks(cluster=cluster_name, tasks=[task_arn])
        for task in response["tasks"]:
            if task["taskDefinitionArn"] == task_definition_arn:
                return task["taskArn"]


def terminate_task(cluster, task_arn, reason):
    logging.info(
        "terminating task cluster:%s arn:%s reason:%s" % (cluster, task_arn, reason)
    )
    response = ecs_client.stop_task(cluster=cluster, task=task_arn, reason=reason)


def terminate(success):
    cluster_name = os.environ.get("ECS_CLUSTER")
    task_definition_name = os.environ.get("TASK_DEFINITION_NAME")
    task_arn = get_task_arn(cluster_name, task_definition_name)
    if task_arn:
        terminate_task(
            cluster_name, task_arn, "Queue drained" if success else "Timeout"
        )
    else:
        logging.error("Running task not found")


def configure_logging():
    logging.basicConfig(
        level=logging.DEBUG if "DEBUG" in os.environ else logging.INFO,
        format="%(asctime)s - %(message)s",
        datefmt="%H:%M:%S",
    )
    logging.getLogger(
        "botocore.vendored.requests.packages.urllib3.connectionpool"
    ).setLevel(logging.WARNING)
    logging.getLogger("requests.packages.urllib3.connectionpool").setLevel(
        logging.WARNING
    )
    logging.getLogger("botocore.credentials").setLevel(logging.WARNING)


if __name__ == "__main__":
    configure_logging()
    for key in (
        "rabbitmq_management_host",
        "rabbitmq_management_user",
        "rabbitmq_management_password",
        "ECS_CLUSTER",
        "TASK_DEFINITION_NAME",
    ):
        if key not in os.environ:
            logging.error("Required environment variable %s not definied" % key)
            sys.exit(-1)

    sleep_interval = int(
        os.environ.get("SLEEP_INTERVAL", 15)
    )  # check often in case things finish quickly
    timeout = int(os.environ.get("TIMEOUT", 60 * 60 * 24 * 2))
    queue_had_messages = False
    elapsed = 0
    while True:
        depths = get_queue_depths(
            os.environ.get("rabbitmq_management_host"),
            os.environ.get("rabbitmq_management_user"),
            os.environ.get("rabbitmq_management_password"),
            os.environ.get("rabbitmq_vhost", "/"),
        )
        message_count = sum(depths.values())
        logging.debug("Message count: %i" % message_count)
        if queue_had_messages == False and message_count > 0:
            logging.info("Found messages in queue")
            queue_had_messages = True
        elif queue_had_messages and message_count <= 0:
            logging.info("Queue has drained, terminating")
            terminate(True)
            sys.exit(0)
        elif elapsed > timeout:
            logging.info("Timeout exceeded, terminating")
            terminate(False)
            sys.exit(0)
        else:
            logging.debug("Sleeping")
            sleep(sleep_interval)
            elapsed += sleep_interval
