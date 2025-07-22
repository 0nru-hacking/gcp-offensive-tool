import subprocess
import os

def safe_run(cmd, description):
    print(f"\n[-] {description}")
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True, text=True)
        print(output)
    except subprocess.CalledProcessError as e:
        if "NOT_FOUND" in e.output or "does not exist" in e.output:
            print(f"⚠️ Resource not found. Skipping: {description}")
        else:
            print(f"❌ Error: {e.output}")

# Config
PROJECT = "poc-tfm-tests"
REGION = "us-central1"
QUEUE = "attacker-queue-tests-tfm"
SERVICE = "private-api"
VICTIM_SA = "victim-sa-test"              # ← Cuenta que debe borrarse
ATTACKER_SA = "attacker-sa-test"          # ← Cuenta atacante, opcional borrar

# Delete dynamically generated Cloud Tasks queue
try:
    with open("modules/abuse_cloud_tasks/queue_id.txt", "r") as f:
        dynamic_queue = f.read().strip()
        safe_run(
            f"gcloud tasks queues delete {dynamic_queue} "
            f"--location={REGION} --quiet --project={PROJECT}",
            f"Deleting dynamic Cloud Tasks queue: {dynamic_queue}"
        )
except FileNotFoundError:
    print("[-] Queue ID file not found. Skipping dynamic queue deletion.")

# 2. Delete Cloud Run service
safe_run(
    f"gcloud run services delete {SERVICE} --region={REGION} --quiet --project={PROJECT}",
    f"Deleting Cloud Run service: {SERVICE}"
)

# 3. Delete victim service account (yes)
safe_run(
    f"gcloud iam service-accounts delete {VICTIM_SA}@{PROJECT}.iam.gserviceaccount.com --quiet",
    f"Deleting victim service account: {VICTIM_SA}"
)

#4. Delete attacker service account (optional, puede omitirse)
safe_run(
    f"gcloud iam service-accounts delete {ATTACKER_SA}@{PROJECT}.iam.gserviceaccount.com --quiet",
    f"Deleting attacker service account: {ATTACKER_SA}"
)

# 5. Delete local key files (except internal-support)
print("\n[-] Deleting local keys if present...")
paths = [
    "attacker-key.json"
]
for path in paths:
    if os.path.exists(path):
        os.remove(path)
        print(f"✔️ Deleted: {path}")
    else:
        print(f"⚠️ Key not found (already deleted?): {path}")

print("\n[✔] Cleanup completed.")
