# modules/abuse_composer_external_payload/1_create_env.py
import os
import subprocess
import sys
import time

PROJECT_ID = "poc-tfm-tests"
REGION = "us-central1"
DEFAULT_ENV_NAME = "tfm-composer-env"

# SA privilegiada (control-plane)
PRIV_SA_EMAIL = "internal-support@poc-tfm-tests.iam.gserviceaccount.com"
PRIV_SA_KEY   = "internal-support-key.json"

# SA atacante (para subir DAG/payload)
ATTACKER_SA = "composer-payload-attacker"
ATTACKER_SA_EMAIL = f"{ATTACKER_SA}@{PROJECT_ID}.iam.gserviceaccount.com"
ATTACKER_SA_KEY = "composer-payload-attacker.json"

# Secreto de demo
SECRET_NAME = "test-secret"
SECRET_VALUE = "Admin Token: 12345678"

USE_EXISTING = False
ENV_NAME = DEFAULT_ENV_NAME

if "--use-existing" in sys.argv:
    i = sys.argv.index("--use-existing")
    if i + 1 < len(sys.argv):
        ENV_NAME = sys.argv[i + 1]
        USE_EXISTING = True


# ---------------- helpers ----------------
def run(cmd, check=True, capture=False):
    print(f"[+] Running: {cmd}")
    if capture:
        p = subprocess.run(cmd, shell=True, text=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if check and p.returncode != 0:
            print("[!] Error executing command.")
            print(p.stderr.strip())
            sys.exit(1)
        return p
    else:
        p = subprocess.run(cmd, shell=True)
        if check and p.returncode != 0:
            print("[!] Error executing command.")
            sys.exit(1)
        return p

def auth_privileged():
    print("[*] Authenticating as privileged service account …")
    run(
        f"gcloud auth activate-service-account {PRIV_SA_EMAIL} "
        f"--key-file={PRIV_SA_KEY} --project={PROJECT_ID}"
    )
    print("[✓] Authenticated.")

def get_project_number():
    r = run(f"gcloud projects describe {PROJECT_ID} --format='value(projectNumber)'",
            capture=True)
    pn = (r.stdout or "").strip()
    if not pn:
        print("[!] Could not get project number.")
        sys.exit(1)
    return pn

def env_exists():
    return subprocess.run(
        f"gcloud composer environments describe {ENV_NAME} "
        f"--location={REGION} --project={PROJECT_ID}",
        shell=True
    ).returncode == 0


# ---------------- worker SA / composer agent ----------------
def ensure_worker_sa():
    """
    Crea (si no existe) una SA para los workers y le concede roles mínimos.
    Devuelve su email.
    """
    worker_id = "tfm-composer-worker"
    worker_sa = f"{worker_id}@{PROJECT_ID}.iam.gserviceaccount.com"

    exists = subprocess.run(
        f"gcloud iam service-accounts describe {worker_sa} --project={PROJECT_ID}",
        shell=True
    ).returncode == 0
    if not exists:
        run(
            f"gcloud iam service-accounts create {worker_id} "
            f"--project={PROJECT_ID} --display-name='TFM Composer Worker SA'"
        )

    # Rol requerido por Composer v2 en la SA de worker
    run(
        f"gcloud projects add-iam-policy-binding {PROJECT_ID} "
        f"--member='serviceAccount:{worker_sa}' "
        f"--role='roles/composer.worker'"
    )
    return worker_sa

def allow_composer_to_act_as(worker_sa, project_number):
    """
    La service-agent de Composer necesita poder 'usar' la SA de worker.
    """
    composer_agent = f"service-{project_number}@cloudcomposer-accounts.iam.gserviceaccount.com"
    run(
        f"gcloud iam service-accounts add-iam-policy-binding {worker_sa} "
        f"--member='serviceAccount:{composer_agent}' "
        f"--role='roles/iam.serviceAccountUser' "
        f"--project={PROJECT_ID}"
    )


# ---------------- environment creation / details ----------------
def create_composer_env(worker_sa):
    if env_exists():
        print(f"[i] Environment {ENV_NAME} already exists. Reusing it.")
        return
    print("[*] Creating new Composer environment…")
    run(
        f"gcloud composer environments create {ENV_NAME} "
        f"--location={REGION} --project={PROJECT_ID} "
        f"--service-account={worker_sa} "
        f"--environment-size=small "
        f"--airflow-configs=core-dags_are_paused_at_creation=False"
    )
    print("[✓] Composer environment created.")

def get_dag_bucket():
    r = run(
        f"gcloud composer environments describe {ENV_NAME} "
        f"--location={REGION} --project={PROJECT_ID} "
        f"--format='value(config.dagGcsPrefix)'",
        capture=True
    )
    dag_prefix = (r.stdout or "").strip()
    if not dag_prefix:
        print("[!] Failed to retrieve DAG bucket.")
        sys.exit(1)
    return dag_prefix.replace('gs://', '').split('/')[0]

def get_env_worker_sas():
    """
    Devuelve el conjunto de SAs que pueden ejecutar DAGs en el entorno:
    - config.workloads.serviceAccount (Composer 2)
    - config.nodeConfig.serviceAccount (compatibilidad)
    """
    sas = set()

    r1 = subprocess.run(
        ["gcloud","composer","environments","describe", ENV_NAME,
         f"--location={REGION}", f"--project={PROJECT_ID}",
         "--format=value(config.workloads.serviceAccount)"],
        text=True, stdout=subprocess.PIPE
    )
    w = (r1.stdout or "").strip()
    if w:
        sas.add(w)

    r2 = subprocess.run(
        ["gcloud","composer","environments","describe", ENV_NAME,
         f"--location={REGION}", f"--project={PROJECT_ID}",
         "--format=value(config.nodeConfig.serviceAccount)"],
        text=True, stdout=subprocess.PIPE
    )
    n = (r2.stdout or "").strip()
    if n:
        sas.add(n)

    return sas


# ---------------- secret creation & grants ----------------
def create_secret_if_needed():
    print(f"[*] Creating secret '{SECRET_NAME}' if needed…")
    exists = subprocess.run(
        f"gcloud secrets describe {SECRET_NAME} --project={PROJECT_ID}",
        shell=True
    ).returncode == 0
    if not exists:
        run(
            f"gcloud secrets create {SECRET_NAME} "
            f"--replication-policy=automatic --project={PROJECT_ID}"
        )
        print("[✓] Secret created.")
    else:
        print("[i] Secret already exists.")

    run(
        f"echo '{SECRET_VALUE}' | "
        f"gcloud secrets versions add {SECRET_NAME} --data-file=- --project={PROJECT_ID}"
    )
    print("[✓] Secret version added.")

def grant_secret_to_worker_sas(extra_sa=None):
    """
    Concede roles/secretmanager.secretAccessor al/los worker SA reales del entorno
    (workloads SA y/o nodeConfig SA). Permite además pasar una SA extra (p.ej. la
    que acabamos de crear explícitamente) para garantizar el acceso.
    """
    sas = get_env_worker_sas()
    if extra_sa:
        sas.add(extra_sa)

    if not sas:
        print("[!] Could not determine any worker service account from Composer env.")
        sys.exit(1)

    print("[*] Granting Secret access to worker SA(s)…")
    for sa in sorted(sas):
        print(f"    - binding to {sa}")
        run(
            f"gcloud secrets add-iam-policy-binding {SECRET_NAME} "
            f"--member='serviceAccount:{sa}' "
            f"--role='roles/secretmanager.secretAccessor' "
            f"--project={PROJECT_ID}"
        )
    print("[✓] Secret accessor granted.")


# ---------------- attacker SA (upload to bucket) ----------------
def prepare_attacker_sa(bucket_name):
    print("[*] Creating or reusing attacker service account …")
    exists = subprocess.run(
        f"gcloud iam service-accounts list --project={PROJECT_ID} "
        f"--filter='email:{ATTACKER_SA_EMAIL}' --format='value(email)'",
        shell=True, capture_output=True, text=True
    ).stdout.strip()
    if not exists:
        run(
            f"gcloud iam service-accounts create {ATTACKER_SA} "
            f"--project={PROJECT_ID} "
            f"--description='Attacker Composer External Payload' "
            f"--display-name='Attacker Composer SA'"
        )
        # pequeña espera de propagación
        for _ in range(30):
            if subprocess.run(
                f"gcloud iam service-accounts describe {ATTACKER_SA_EMAIL} --project={PROJECT_ID}",
                shell=True
            ).returncode == 0:
                break
            time.sleep(2)

    run(
        f"gcloud projects add-iam-policy-binding {PROJECT_ID} "
        f"--member='serviceAccount:{ATTACKER_SA_EMAIL}' "
        f"--role='roles/storage.objectAdmin'"
    )
    run(
        f"gcloud projects add-iam-policy-binding {PROJECT_ID} "
        f"--member='serviceAccount:{ATTACKER_SA_EMAIL}' "
        f"--role='roles/viewer'"
    )
    run(
        f"gsutil iam ch serviceAccount:{ATTACKER_SA_EMAIL}:roles/storage.objectCreator "
        f"gs://{bucket_name}"
    )
    if not os.path.exists(ATTACKER_SA_KEY):
        run(
            f"gcloud iam service-accounts keys create {ATTACKER_SA_KEY} "
            f"--iam-account={ATTACKER_SA_EMAIL} --project={PROJECT_ID}"
        )
    run(
        f"gcloud auth activate-service-account {ATTACKER_SA_EMAIL} "
        f"--key-file={ATTACKER_SA_KEY} --project={PROJECT_ID}"
    )
    print("[✓] Attacker service account ready.")


# ---------------- main ----------------
def main():
    auth_privileged()
    project_number = get_project_number()

    # 1) SA de worker y permisos necesarios
    worker_sa = ensure_worker_sa()
    allow_composer_to_act_as(worker_sa, project_number)

    # 2) Crear entorno (si no existe), usando explícitamente la SA de worker
    if not USE_EXISTING:
        create_composer_env(worker_sa)
    else:
        print(f"[v] Reusing existing Composer environment: {ENV_NAME}")

    # 3) Secreto + concesión de acceso a las SAs que ejecutan los tasks
    create_secret_if_needed()
    # Concedemos al conjunto real del entorno + nuestra worker_sa explícita
    grant_secret_to_worker_sas(extra_sa=worker_sa)

    # 4) SA atacante y permisos para subir al bucket de DAGs
    bucket = get_dag_bucket()
    prepare_attacker_sa(bucket)

if __name__ == "__main__":
    main()
