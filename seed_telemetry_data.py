import boto3
import json
import time
import random
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load credentials from .env file (safest method for local dev/demo)
load_dotenv()

# --- Zero-Cost Configuration ---
REGION = os.getenv("AWS_DEFAULT_REGION", "ap-south-1")
LOG_GROUP_NAME = "Filegroup/processor" # Existing log group
RETENTION_DAYS = 3
SERVICE_NAME = "aura-guard-node-service"
ENVIRONMENT = "production"

# Initialize Clients using credentials from .env or Environment Variables
cw_logs = boto3.client(
    'logs', 
    region_name=REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
)
cw_metrics = boto3.client(
    'cloudwatch', 
    region_name=REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
)

def setup_log_stream():
    """Ensure a specific log stream exists for the demo."""
    stream_name = f"triage-demo-{int(time.time())}"
    try:
        cw_logs.create_log_stream(logGroupName=LOG_GROUP_NAME, logStreamName=stream_name)
        print(f"Created Log Stream: {stream_name}")
    except Exception as e:
        print(f"Note: {e}")
    return stream_name

def push_incident_telemetry():
    """
    Simulates a production incident:
    1. A CPU Spike metric.
    2. Multiple ERROR logs indicating a timeout/memory issue.
    This data is designed to be picked up by the Aura Guard 'Incident Triage' feature.
    """
    stream_name = setup_log_stream()
    timestamp = int(round(time.time() * 1000))

    # 1. PUSH METRIC: CPU Spike (Simulating 92% utilization)
    # We use static dimensions to keep this in the Always Free Tier.
    cw_metrics.put_metric_data(
        Namespace="AuraGuard/Infrastructure",
        MetricData=[
            {
                'MetricName': 'CPUUtilization',
                'Dimensions': [
                    {'Name': 'ServiceName', 'Value': SERVICE_NAME},
                    {'Name': 'Cluster', 'Value': 'Aura-Prod-Cluster'}
                ],
                'Value': 92.5,
                'Unit': 'Percent',
                'Timestamp': datetime.now(timezone.utc)
            }
        ]
    )
    print("Metric Pushed: CPUUtilization spiked to 92.5%")

    # 2. PUSH ERROR LOGS: Structured JSON for the Agent to SQL-query
    # We include 'commit_sha' and a detailed stack trace for deep correlation
    incident_logs = [
        {
            "level": "ERROR",
            "service": SERVICE_NAME,
            "error_code": "E_OOM_CRASH",
            "message": "Process terminated: Out of memory in 'lodash' optimization loop",
            "stack_trace": "Error: Out of memory\n    at optimizeChunk (src/processor.js:42:12)\n    at processBatch (src/processor.js:15:5)\n    at Object.<anonymous> (src/index.js:8:1)",
            "properties": {
                "traceId": "triage-12345",
                "commit_sha": "fff1eb69e56e0411bec812b77105b1cd0873d406",
                "component": "processor",
                "file": "src/processor.js",
                "line": 42,
                "vulnerable_pkg": "lodash@4.17.21"
            }
        },
        {
            "level": "ERROR",
            "service": SERVICE_NAME,
            "error_code": "ETIMEDOUT",
            "message": "Connection timeout during dependency resolution",
            "properties": {
                "traceId": "triage-12345",
                "commit_sha": "fff1eb69e56e0411bec812b77105b1cd0873d406",
                "component": "ingestion-engine"
            }
        }
    ]

    log_events = []
    for i, log in enumerate(incident_logs):
        log_events.append({
            'timestamp': timestamp + (i * 100), # Slight offset
            'message': json.dumps(log)
        })

    cw_logs.put_log_events(
        logGroupName=LOG_GROUP_NAME,
        logStreamName=stream_name,
        logEvents=log_events
    )
    print(f"🚨 {len(log_events)} Error Logs pushed to {LOG_GROUP_NAME}")

if __name__ == "__main__":
    # --- DO NOT AUTO-EXECUTE ---
    # To run this for the demo, ensure your AWS credentials are set and call:
    push_incident_telemetry()
    print("Aura Guard Telemetry Seeder Ready.")
    print("Target Group: Filegroup/processor (ap-south-1)")
    print("Workflows: [Incident Triage Demo, Infrastructure Monitoring]")
    pass
