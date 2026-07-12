"""
Cross-Region CloudWatch Logs Replicator

Receives log events from a CloudWatch Logs subscription filter
and forwards them to a log group in another region.
"""

import base64
import gzip
import json
import os
import time

import boto3

DEST_REGION = os.environ["DEST_REGION"]
DEST_LOG_GROUP = os.environ["DEST_LOG_GROUP"]
DEST_LOG_STREAM = os.environ["DEST_LOG_STREAM"]
ALLOWED_SOURCE_STREAMS = os.environ.get("ALLOWED_SOURCE_STREAMS", "").split(",")


logs_client = boto3.client("logs", region_name=DEST_REGION)


def ensure_log_stream(log_group: str, log_stream: str) -> None:
    try:
        logs_client.create_log_stream(
            logGroupName=log_group,
            logStreamName=log_stream,
        )
    except logs_client.exceptions.ResourceAlreadyExistsException:
        pass


def handler(event, context):
    payload = base64.b64decode(event["awslogs"]["data"])
    log_data = json.loads(gzip.decompress(payload))

    if log_data.get("messageType") == "CONTROL_MESSAGE":
        print("Control message received, skipping.")
        return {"statusCode": 200, "body": "Control message, skipped."}

    source_stream = log_data.get("logStream", "")
    if ALLOWED_SOURCE_STREAMS and ALLOWED_SOURCE_STREAMS != [""] and source_stream not in ALLOWED_SOURCE_STREAMS:
        print(f"Skipping stream '{source_stream}', not in allowed list: {ALLOWED_SOURCE_STREAMS}")
        return {"statusCode": 200, "body": f"Skipped stream: {source_stream}"}

    log_events = log_data.get("logEvents", [])
    if not log_events:
        print("No log events to forward.")
        return {"statusCode": 200, "body": "No events."}

    ensure_log_stream(DEST_LOG_GROUP, DEST_LOG_STREAM)

    # CloudWatch PutLogEvents accepts max 10,000 events / 1 MB per call
    batch_size = 10000
    for i in range(0, len(log_events), batch_size):
        batch = log_events[i : i + batch_size]
        events = [
            {"timestamp": e["timestamp"], "message": e["message"]}
            for e in batch
        ]
        events.sort(key=lambda e: e["timestamp"])

        logs_client.put_log_events(
            logGroupName=DEST_LOG_GROUP,
            logStreamName=DEST_LOG_STREAM,
            logEvents=events,
        )

    forwarded = len(log_events)
    source = f"{log_data.get('logGroup')}:{log_data.get('logStream')}"
    print(f"Forwarded {forwarded} events from {source} -> {DEST_LOG_GROUP}:{DEST_LOG_STREAM}")

    return {"statusCode": 200, "body": f"Forwarded {forwarded} events."}
