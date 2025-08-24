import subprocess
import sys

PROJECT_ID = "poc-tfm-tests"
LOCATION = "us-central1"
ENV_NAME = "tfm-composer-env"   # corregido
DAG_NAME = "persistent_escalated_dag"
SA_NAME = "composer-sa"
SA_EMAIL = f"{SA_NAME}@{PROJECT_ID}.iam.gserviceaccount.com"

def run_cmd(cmd, error_msg):
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[!] {error_msg}")
        print(e)
        sys.exit(1)

# 0. Pausar DAG antes de borrar el entorno
print("[*] Pausing malicious DAG before cleanup...")
run_cmd([
    "gcloud", "composer", "environments", "run", ENV_NAME,
    "--location", LOCATION, "--project", PROJECT_ID,
    "dags", "pause", "--", DAG_NAME
], "Failed to pause DAG.")

# 1. Delete Composer environment
print("[*] Deleting Composer environment...")
run_cmd([
    "gcloud", "composer", "environments", "delete", ENV_NAME,
    "--location", LOCATION,
    "--project", PROJECT_ID,
    "--quiet"
], "Failed to delete Composer environment.")

# 2. Remove role bindings
print("[*] Removing role bindings from Composer SA...")
run_cmd([
    "gcloud", "projects", "remove-iam-policy-binding", PROJECT_ID,
    "--member", f"serviceAccount:{SA_EMAIL}",
    "--role", "roles/composer.worker"
], "Failed to remove IAM role from Composer SA.")

# 3. Delete the service account
print("[*] Deleting Composer service account...")
run_cmd([
    "gcloud", "iam", "service-accounts", "delete", SA_EMAIL,
    "--project", PROJECT_ID,
    "--quiet"
], "Failed to delete Composer SA.")

print("[✓] Cleanup finished successfully.")
