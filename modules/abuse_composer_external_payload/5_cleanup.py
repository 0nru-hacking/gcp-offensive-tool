# modules/abuse_composer_external_payload/5_cleanup.py
import subprocess
import sys

PROJECT_ID = "poc-tfm-tests"
REGION = "us-central1"
ENV_NAME = "tfm-composer-env"
DAG_NAME = "persistent_escalated_dag"

ATTACKER_SA_EMAIL = f"composer-payload-attacker@{PROJECT_ID}.iam.gserviceaccount.com"
SECRET_NAME = "test-secret"

OWNER_SA  = "internal-support@poc-tfm-tests.iam.gserviceaccount.com"
OWNER_KEY = "internal-support-key.json"

# Si cambiaste nombres/ubicaciones en tu execute_attack, ajusta:
DAG_OBJECT = "dags/malicious_dag_external.py"
PAYLOAD_OBJECT = "payloads/payload.py"

AIRFLOW_VARS = ["WEBHOOK_URL", "PAYLOAD_URL", "SECRET_NAME", "GCP_PROJECT"]

def run_cmd(args, check=True):
    if isinstance(args, str):
        print(f"[+] Running: {args}")
        r = subprocess.run(args, shell=True)
    else:
        print(f"[+] Running: {' '.join(args)}")
        r = subprocess.run(args)
    if check and r.returncode != 0:
        print("[!] Error executing command.")
        sys.exit(1)
    return r

def auth_owner():
    print("[*] Authenticating as privileged SA …")
    run_cmd([
        "gcloud","auth","activate-service-account", OWNER_SA,
        "--key-file", OWNER_KEY, f"--project={PROJECT_ID}"
    ])
    print("[✓] Authenticated.")

def env_exists():
    return subprocess.run(
        ["gcloud","composer","environments","describe",ENV_NAME,
         "--location",REGION,"--project",PROJECT_ID],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    ).returncode == 0

def get_worker_sa():
    r = subprocess.run(
        ["gcloud","composer","environments","describe",ENV_NAME,
         "--location",REGION,"--project",PROJECT_ID,
         "--format=value(config.nodeConfig.serviceAccount,config.workloads.serviceAccount)"],
        text=True, stdout=subprocess.PIPE
    )
    return (r.stdout or "").strip()

def get_dag_bucket():
    r = subprocess.run(
        ["gcloud","composer","environments","describe",ENV_NAME,
         "--location",REGION,"--project",PROJECT_ID,
         "--format=value(config.dagGcsPrefix)"],
        text=True, stdout=subprocess.PIPE
    )
    dag_prefix = (r.stdout or "").strip()
    if not dag_prefix:
        return None
    return dag_prefix.replace("gs://", "").split("/")[0]

def pause_dag():
    print("[*] Pausing DAG (idempotent)…")
    run_cmd([
        "gcloud","composer","environments","run",ENV_NAME,
        "--location",REGION,"--project",PROJECT_ID,
        "dags","pause","--",DAG_NAME
    ], check=False)

def delete_airflow_vars():
    print("[*] Deleting Airflow Variables (best effort)…")
    for k in AIRFLOW_VARS:
        run_cmd([
            "gcloud","composer","environments","run",ENV_NAME,
            "--location",REGION,"--project",PROJECT_ID,
            "variables","delete","--",k
        ], check=False)

def remove_gcs_artifacts(bucket):
    if not bucket:
        return
    print(f"[*] Removing DAG/payload objects from gs://{bucket} (best effort)…")
    run_cmd(
        f"gsutil -o GSUtil:default_project_id={PROJECT_ID} rm -f gs://{bucket}/{DAG_OBJECT}",
        check=False
    )
    run_cmd(
        f"gsutil -o GSUtil:default_project_id={PROJECT_ID} rm -f gs://{bucket}/{PAYLOAD_OBJECT}",
        check=False
    )

def remove_secret_binding(worker_sa):
    if not worker_sa:
        return
    print(f"[*] Removing Secret accessor from worker SA: {worker_sa}")
    run_cmd([
        "gcloud","secrets","remove-iam-policy-binding", SECRET_NAME,
        "--member", f"serviceAccount:{worker_sa}",
        "--role", "roles/secretmanager.secretAccessor",
        f"--project={PROJECT_ID}"
    ], check=False)

def remove_bucket_binding(bucket):
    if not bucket:
        return
    print(f"[*] Removing bucket IAM binding for attacker SA on gs://{bucket} …")
    run_cmd(
        f"gsutil -o GSUtil:default_project_id={PROJECT_ID} "
        f"iam ch -d serviceAccount:{ATTACKER_SA_EMAIL}:roles/storage.objectCreator "
        f"gs://{bucket}",
        check=False
    )

def remove_project_roles():
    print("[*] Removing project-level roles from attacker SA…")
    for role in ("roles/storage.objectAdmin","roles/viewer"):
        run_cmd([
            "gcloud","projects","remove-iam-policy-binding", PROJECT_ID,
            "--member", f"serviceAccount:{ATTACKER_SA_EMAIL}",
            "--role", role
        ], check=False)

def delete_attacker_sa():
    print("[*] Deleting attacker service account (best effort)…")
    run_cmd([
        "gcloud","iam","service-accounts","delete", ATTACKER_SA_EMAIL,
        "--project",PROJECT_ID,"--quiet"
    ], check=False)

if __name__ == "__main__":
    auth_owner()

    worker_sa = None
    bucket = None
    if env_exists():
        worker_sa = get_worker_sa() or None
        bucket = get_dag_bucket() or None
        pause_dag()
        delete_airflow_vars()
    else:
        print(f"[i] Environment '{ENV_NAME}' not found; skipping Composer-side cleanup.")

    remove_secret_binding(worker_sa)
    remove_bucket_binding(bucket)
    remove_project_roles()
    remove_gcs_artifacts(bucket)
    delete_attacker_sa()

    print("[✓] Cleanup finished (Composer env preserved).")
