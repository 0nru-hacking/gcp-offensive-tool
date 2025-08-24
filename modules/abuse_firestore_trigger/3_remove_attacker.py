import subprocess
import os

# === CONFIG ===
PROJECT_ID = "poc-tfm-tests"
ATTACKER_SA = "attacker-sa"
KEY_FILE = os.path.join(os.path.dirname(__file__), "attacker-sa-key.json")

# === 1. Eliminar la clave JSON de attacker-sa ===
print("[1/3] Deleting service account key file...")
if os.path.exists(KEY_FILE):
    os.remove(KEY_FILE)
    print(f"[✓] Deleted local key file: {KEY_FILE}")
else:
    print("[i] Key file already removed.")

# === 2. Revocar todos los roles (por limpieza) ===
print("[2/3] Revoking IAM roles (if still assigned)...")
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

print("[✓] IAM bindings revoked.")

# === 3. Eliminar la service account ===
print("[3/3] Deleting attacker service account...")
subprocess.run([
    "gcloud", "iam", "service-accounts", "delete",
    f"{ATTACKER_SA}@{PROJECT_ID}.iam.gserviceaccount.com",
    "--quiet"
], check=True)

print("[✔] Attacker service account fully deleted.")
