import subprocess
import os
import time
from core.config import REGION

OWNER_KEY_FILE = "internal-support-key.json"
ATTACKER_KEY_FILE = "attacker-key.json"

def run_command(command, capture_output=False):
    auth_env = os.environ.copy()
    auth_env["GOOGLE_APPLICATION_CREDENTIALS"] = OWNER_KEY_FILE

    full_command = f"gcloud auth activate-service-account --key-file={OWNER_KEY_FILE} --quiet && {command}"

    try:
        if capture_output:
            result = subprocess.run(full_command, shell=True, check=True, text=True,
                                    capture_output=True, env=auth_env)
            return result.stdout.strip()
        else:
            subprocess.run(full_command, shell=True, check=True, env=auth_env)
    except subprocess.CalledProcessError as e:
        print(f"Error running owner command: {command}")
        print(e.stderr if hasattr(e, 'stderr') else str(e))
        exit(1)

def run_command_as_attacker(command, capture_output=False):
    auth_env = os.environ.copy()
    auth_env["GOOGLE_APPLICATION_CREDENTIALS"] = ATTACKER_KEY_FILE

    full_command = f"gcloud auth activate-service-account --key-file={ATTACKER_KEY_FILE} --quiet && {command}"

    try:
        if capture_output:
            result = subprocess.run(full_command, shell=True, check=True, text=True,
                                    capture_output=True, env=auth_env)
            return result.stdout.strip()
        else:
            subprocess.run(full_command, shell=True, check=True, env=auth_env)
    except subprocess.CalledProcessError as e:
        print(f"Error running attacker command: {command}")
        print(e.stderr if hasattr(e, 'stderr') else str(e))
        exit(1)


def enable_apis(project_id, apis):
    for api in apis:
        print(f"Enabling API: {api}")
        run_command(f"gcloud services enable {api} --project={project_id}")
        time.sleep(2)  # Optional: delay to avoid quota errors

def create_service_account(project_id, sa_name, description=""):
    print(f"Creating service account: {sa_name}")
    run_command(f"gcloud iam service-accounts create {sa_name} "
                f"--project={project_id} "
                f"--description='{description}'")

def grant_role_to_sa(project_id, sa_name, role):
    print(f"Granting role {role} to {sa_name}")
    full_sa = f"{sa_name}@{project_id}.iam.gserviceaccount.com"
    run_command(f"gcloud projects add-iam-policy-binding {project_id} "
                f"--member='serviceAccount:{full_sa}' "
                f"--role='{role}'")

def allow_impersonation(project_id, impersonator, target):
    print(f"Allowing {impersonator} to impersonate {target}")
    impersonator_sa = f"serviceAccount:{impersonator}@{project_id}.iam.gserviceaccount.com"
    target_sa = f"{target}@{project_id}.iam.gserviceaccount.com"
    run_command(f"gcloud iam service-accounts add-iam-policy-binding {target_sa} "
                f"--member='{impersonator_sa}' "
                f"--role='roles/iam.serviceAccountTokenCreator' "
                f"--project={project_id}")

def deploy_private_cloud_run(project_id, region, service_name, sa_name):
    print(f"Deploying private Cloud Run service: {service_name}")
    run_command(
        f"gcloud run deploy {service_name} "
        f"--image=gcr.io/{project_id}/cloudrun-sensitive-service "
        f"--no-allow-unauthenticated "
        f"--region={region} "
        f"--project={project_id} "
        f"--service-account={sa_name}@{project_id}.iam.gserviceaccount.com"
    )

def create_cloud_tasks_queue(project_id, region, queue_name):
    print(f"Creating Cloud Tasks queue: {queue_name}")
    run_command(
        f"gcloud tasks queues create {queue_name} "
        f"--location={region} "
        f"--project={project_id}"
    )

def get_cloud_run_url(project_id, region="us-central1", service_name="private-api"):
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
        print(f"[-] Failed to get Cloud Run URL: {e.stderr}")
        return None
