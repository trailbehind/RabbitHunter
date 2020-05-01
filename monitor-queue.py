#!/usr/bin/env python3
import logging
import os
import sys
from datetime import datetime
from time import sleep

from pyrabbit.api import Client


def get_queue_depths(host, username, password, vhost):
    cl = Client(host + "/api/", username, password)
    if not cl.is_alive():
        raise Exception("Failed to connect to rabbitmq")
    depths = {}
    queues = [q["name"] for q in cl.get_queues(vhost=vhost)]
    for queue in queues:
        if queue == "aliveness-test":
            continue
        depths[queue] = cl.get_queue_depth(vhost, queue)
    return depths


def configure_logging():
    logging.basicConfig(
        level=logging.DEBUG if "DEBUG" in os.environ else logging.INFO,
        format="%(asctime)s - %(message)s",
        datefmt="%H:%M:%S",
    )
    # Turn down boto logging
    logging.getLogger(
        "botocore.vendored.requests.packages.urllib3.connectionpool"
    ).setLevel(logging.WARNING)
    logging.getLogger("botocore.credentials").setLevel(logging.WARNING)
    # Turn down pyrabbit logging
    logging.getLogger("requests.packages.urllib3.connectionpool").setLevel(
        logging.WARNING
    )
    logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)


if __name__ == "__main__":
    configure_logging()
    for key in (
        "rabbitmq_management_host",
        "rabbitmq_management_user",
        "rabbitmq_management_password",
    ):
        if key not in os.environ:
            logging.error("Required environment variable %s not definied" % key)
            sys.exit(-1)

    start = datetime.now()

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
        elapsed = datetime.now() - start
        logging.debug("Message count: %i" % message_count)
        if queue_had_messages == False and message_count > 0:
            logging.info("Found messages in queue after {}".format(elapsed))
            queue_had_messages = True
        elif queue_had_messages and message_count <= 0:
            logging.info("Queue has drained, exiting. Total runtime {}".format(elapsed))
            sys.exit(0)
        elif elapsed.total_seconds() > timeout:
            logging.info(
                "Timeout exceeded, exiting. {} messages still in queue after {}".format(
                    message_count, elapsed
                )
            )
            sys.exit(-1)
        else:
            logging.debug("Sleeping")
            sleep(sleep_interval)
