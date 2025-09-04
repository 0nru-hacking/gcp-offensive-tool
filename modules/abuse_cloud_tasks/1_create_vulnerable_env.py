#!/usr/bin/env python3

import subprocess
import time
from uuid import uuid4
from core.gcp_utils import (
    enable_apis,
    create_service_account,
    grant_role_to_sa,
    allow_impersonation,
    deploy_private_cloud_run,
    create_cloud_tasks_queue,
)
from core.config import PROJECT_ID, REGION
from core.gcp_utils import run_command_as_attacker, run_command, get_cloud_run_url

def build_and_push_docker_image():
    print("[*] Building and pushing Docker image for Cloud Run...")
    docker_dir = "cloudrun_api"
    image_name = "cloudrun-sensitive-service"
    cmd = (
        f"gcloud builds submit {docker_dir} "
        f"--tag gcr.io/{PROJECT_ID}/{image_name} "
        f"--project={PROJECT_ID}"
    )
    run_command(cmd)
    print("[✓] Docker image built and pushed.")

def get_service_url(project_id, region="us-central1", service_name="private-api"):
    try:
        result = subprocess.run(
            [
                "gcloud", "run", "services", "describe", service_name,
                "--platform=managed",
                f"--project={project_id}",
                f"--region={region}",
                "--format=value(status.url)"
            ],
            check=True,
            capture_output=True,
            text=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"[-] Failed to get Service URL: {e.stderr}")
        return None


def main():
    print("Enabling required APIs ...")
    apis = [
        "cloudtasks.googleapis.com",
        "iamcredentials.googleapis.com",
        "iam.googleapis.com",
        "run.googleapis.com",
        "cloudbuild.googleapis.com",
        "artifactregistry.googleapis.com",
        "compute.googleapis.com",
        "servicemanagement.googleapis.com",
        "servicecontrol.googleapis.com"
    ]
    enable_apis(PROJECT_ID, apis)

    print("Creating service accounts ...")
    victim_sa = "victim-sa-test"
    attacker_sa = "attacker-sa-test"
    create_service_account(PROJECT_ID, victim_sa, "Privileged victim")
    create_service_account(PROJECT_ID, attacker_sa, "Attacker identity")

    print("Generating JSON key for attacker service account ...")
    attacker_key_file = "attacker-key.json"
    subprocess.run([
        "gcloud", "iam", "service-accounts", "keys", "create", attacker_key_file,
        "--iam-account", f"{attacker_sa}@{PROJECT_ID}.iam.gserviceaccount.com"
    ], check=True)
    print(f"[✓] Attacker key saved as {attacker_key_file}")

    print("Granting roles to service accounts ...")
    # Victim: Cloud Run Invoker
    grant_role_to_sa(PROJECT_ID, victim_sa, "roles/run.invoker")

    # Attacker: Cloud Tasks Enqueuer
    grant_role_to_sa(PROJECT_ID, attacker_sa, "roles/cloudtasks.admin")

    # Attacker: Can impersonate the victim
    allow_impersonation(PROJECT_ID, impersonator=attacker_sa, target=victim_sa)

    print("Building and pushing Cloud Run image ...")
    build_and_push_docker_image()

    print("Deploying private Cloud Run service ...")
    deploy_private_cloud_run(PROJECT_ID, REGION, "private-api", victim_sa)

    # Recuperar la URL del servicio recién desplegado (como OWNER)
    print("[v] Getting Cloud Run URLs ...")
    real_url = get_service_url(PROJECT_ID, REGION, "private-api")

    if real_url:
        with open("cloud_run_real_url.txt", "w") as f:
            f.write(real_url)
        print(f"[v] Real Cloud Run Service URL saved: {real_url}")
    else:
        print("[-] Could not obtain real Cloud Run Service URL.")


    print("Creating Cloud Tasks queue as attacker...")
    unique_queue_name = f"attacker-queue-{uuid4().hex[:6]}"
    run_command_as_attacker(
        f"gcloud tasks queues create {unique_queue_name} "
        f"--location={REGION} "
        f"--project={PROJECT_ID}"
    )

    with open("modules/abuse_cloud_tasks/queue_id.txt", "w") as f:
        f.write(unique_queue_name)


    print("Environment setup completed.")

if __name__ == "__main__":
    main()
