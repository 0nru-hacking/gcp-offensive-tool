import os
import time
from google.cloud import firestore
from google.auth import default

# === CONFIG ===
PROJECT_ID = "poc-tfm-tests"
COLLECTION = "sensitive-data"

print("[1/2] Using current authenticated account (e.g., internal-support)...")
credentials, _ = default()
print("[✓] Authenticated.")

print("[2/2] Inserting document into Firestore (post-compromise)...")

db = firestore.Client(project=PROJECT_ID, credentials=credentials)

doc_ref = db.collection(COLLECTION).document()
doc_ref.set({
    "data": "executed_after_compromise",
    "source": "internal-support",
    "timestamp": firestore.SERVER_TIMESTAMP
})

print(f"[✓] Document inserted into '{COLLECTION}' collection.")
print("[✔] If function is persistent, you should see the webhook fire again.")
