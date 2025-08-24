import os
import subprocess
import sys
import time

PROJECT_ID = "poc-tfm-tests"
REGION = "us-central1"
DEFAULT_ENV_NAME = "tfm-composer-env"
ATTACKER_SA = "attacker-sa"
ATTACKER_SA_EMAIL = f"{ATTACKER_SA}@{PROJECT_ID}.iam.gserviceaccount.com"
ATTACKER_SA_KEY = "attacker-sa-key.json"
SECRET_NAME = "test-secret"

USE_EXISTING = False
ENV_NAME = DEFAULT_ENV_NAME

# Leer argumento --use-existing si se pasó desde run_attack.py
if "--use-existing" in sys.argv:
    idx = sys.argv.index("--use-existing")
    if idx + 1 < len(sys.argv):
        ENV_NAME = sys.argv[idx + 1]
        USE_EXISTING = True

def run_cmd(cmd, check=True):
    print(f"[+] Running: {cmd}")
    result = subprocess.run(cmd, shell=True)
    if check and result.returncode != 0:
        print("[!] Error executing command.")
        exit(1)

def create_composer_env():
    print("[*] Creating new Composer environment...")
    run_cmd(f"gcloud composer environments create {ENV_NAME} "
            f"--location={REGION} --project={PROJECT_ID} "
            "--runtime-version=2.5.5 --environment-size=small "
            "--airflow-configs=core-dags_are_paused_at_creation=False")
    print("[✓] Composer environment created.")

def get_composer_service_account():
    print("[*] Retrieving Composer Service Account used for DAG execution...")
    result = subprocess.run(
        f"gcloud composer environments describe {ENV_NAME} "
        f"--location={REGION} --format='value(config.nodeConfig.serviceAccount)'",
        shell=True, capture_output=True, text=True
    )
    if result.returncode != 0:
        print("[!] Failed to retrieve Composer SA.")
        exit(1)
    sa_email = result.stdout.strip()
    print(f"[✓] Composer SA: {sa_email}")
    return sa_email

def create_secret(composer_sa_email):
    print(f"[*] Creating secret '{SECRET_NAME}' with dummy value...")
    # Crea si no existe
    result = subprocess.run(
        f"gcloud secrets describe {SECRET_NAME} --project={PROJECT_ID}",
        shell=True
    )
    if result.returncode != 0:
        run_cmd(
            f"gcloud secrets create {SECRET_NAME} "
            f"--replication-policy=automatic --project={PROJECT_ID}"
        )
        print("[✓] Secret created.")
    else:
        print("[i] Secret already exists. Continuing...")

    run_cmd(
        f"echo 'TFM-SECRET-VALUE' | "
        f"gcloud secrets versions add {SECRET_NAME} --data-file=- --project={PROJECT_ID}"
    )
    run_cmd(
        f"gcloud secrets add-iam-policy-binding {SECRET_NAME} "
        f"--member='serviceAccount:{composer_sa_email}' "
        f"--role='roles/secretmanager.secretAccessor' --project={PROJECT_ID}"
    )
    print("[✓] Secret ready and bound to Composer SA.")

def create_attacker_sa():
    print("[*] Creating or reusing attacker service account …")

    # ¿Existe ya?
    exists = subprocess.run(
        f"gcloud iam service-accounts list --project={PROJECT_ID} "
        f"--filter='email:{ATTACKER_SA_EMAIL}' --format='value(email)'",
        shell=True, capture_output=True, text=True
    ).stdout.strip()

    if exists:
        print(f"[i] Service account {ATTACKER_SA_EMAIL} already exists. Reusing it.")
    else:
        run_cmd(
            f"gcloud iam service-accounts create {ATTACKER_SA} "
            f"--project={PROJECT_ID} "
            f"--description='Attacker Service Account for Composer Abuse' "
            f"--display-name='Attacker SA'"
        )

    # Asegura roles a nivel proyecto
    run_cmd(
        f"gcloud projects add-iam-policy-binding {PROJECT_ID} "
        f"--member='serviceAccount:{ATTACKER_SA_EMAIL}' "
        f"--role='roles/storage.objectAdmin'"
    )
    run_cmd(
        f"gcloud projects add-iam-policy-binding {PROJECT_ID} "
        f"--member='serviceAccount:{ATTACKER_SA_EMAIL}' "
        f"--role='roles/viewer'"
    )

    # Crear (o recrear) clave JSON si no existe
    if not os.path.exists(ATTACKER_SA_KEY):
        run_cmd(
            f"gcloud iam service-accounts keys create {ATTACKER_SA_KEY} "
            f"--iam-account={ATTACKER_SA_EMAIL} --project={PROJECT_ID}"
        )
    else:
        print(f"[i] Key file {ATTACKER_SA_KEY} already exists. Keeping it.")

    # Obtener bucket de DAGs
    result = subprocess.run(
        f"gcloud composer environments describe {ENV_NAME} "
        f"--location={REGION} --project={PROJECT_ID} "
        f"--format='value(config.dagGcsPrefix)'",
        shell=True, capture_output=True, text=True
    )
    if result.returncode != 0 or not result.stdout.strip():
        print("[!] Failed to retrieve DAG bucket.")
        exit(1)

    dag_prefix = result.stdout.strip()
    bucket_name = dag_prefix.replace('gs://', '').split('/')[0]
    print(f"[✓] Composer DAG bucket: {bucket_name}")

    # Permiso de subida al bucket
    run_cmd(
        f"gsutil iam ch serviceAccount:{ATTACKER_SA_EMAIL}:roles/storage.objectCreator "
        f"gs://{bucket_name}"
    )

    # Autenticarse con la SA (si así lo quieres en este paso)
    run_cmd(
        f"gcloud auth activate-service-account {ATTACKER_SA_EMAIL} "
        f"--key-file={ATTACKER_SA_KEY} --project={PROJECT_ID}"
    )

    print("[✓] Attacker service account ready.")


def wait_for_service_account(email, timeout=60):
    print(f"[*] Waiting for service account {email} to be ready...")
    for _ in range(timeout):
        result = subprocess.run(
            f"gcloud iam service-accounts describe {email}",
            shell=True, capture_output=True
        )
        if result.returncode == 0:
            print("[✓] Service account is ready.")
            return
        time.sleep(1)
    print("[!] Timeout waiting for service account to be ready.")
    exit(1)

def main():
    if USE_EXISTING:
        print(f"[v] Reusing existing Composer environment: {ENV_NAME}")
    else:
        create_composer_env()

    composer_sa_email = get_composer_service_account()
    create_secret(composer_sa_email)
    create_attacker_sa()
    wait_for_service_account(ATTACKER_SA_EMAIL)

if __name__ == "__main__":
    main()
