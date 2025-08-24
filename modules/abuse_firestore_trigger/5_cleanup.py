import subprocess
import os
import shutil

# === CONFIG ===
PROJECT_ID = "poc-tfm-tests"
REGION = "europe-west1"
FUNCTION_NAME = "firestore-trigger"
ATTACKER_SA = "attacker-sa"
KEY_FILE = os.path.join(os.path.dirname(__file__), "attacker-sa-key.json")
TEMP_DIR = os.path.join(os.path.dirname(__file__), "temp_function")

# === 1. Eliminar función maliciosa ===
print("[1/5] Deleting malicious Cloud Function...")
subprocess.run([
    "gcloud", "functions", "delete", FUNCTION_NAME,
    "--project", PROJECT_ID,
    "--region", REGION,
    "--quiet"
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("[✓] Cloud Function deleted.")

# === 2. Eliminar attacker-sa si existe ===
print("[2/5] Deleting attacker-sa service account (if exists)...")
subprocess.run([
    "gcloud", "iam", "service-accounts", "delete",
    f"{ATTACKER_SA}@{PROJECT_ID}.iam.gserviceaccount.com",
    "--quiet"
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("[✓] Service account deleted.")

# === 3. Eliminar bindings IAM por seguridad ===
print("[3/5] Removing IAM bindings...")
roles = [
    "roles/cloudfunctions.developer",
    "roles/iam.serviceAccountUser",
    "roles/datastore.user"
]

for role in roles:
    subprocess.run([
        "gcloud", "projects", "remove-iam-policy-binding", PROJECT_ID,
        "--member", f"serviceAccount:{ATTACKER_SA}@{PROJECT_ID}.iam.gserviceaccount.com",
        "--role", role
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("[✓] IAM bindings removed.")

# === 4. Borrar clave JSON ===
print("[4/5] Removing local service account key...")
if os.path.exists(KEY_FILE):
    os.remove(KEY_FILE)
    print(f"[✓] Key file deleted: {KEY_FILE}")
else:
    print("[i] Key file not found (may have been deleted already)")

# === 5. Borrar temp_function/ ===
print("[5/5] Deleting temp_function working directory...")
if os.path.exists(TEMP_DIR):
    shutil.rmtree(TEMP_DIR)
    print("[✓] Temp function directory removed.")
else:
    print("[i] Temp directory not found.")

print("\n[✔] Cleanup completed successfully.")
