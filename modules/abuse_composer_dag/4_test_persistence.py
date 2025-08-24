import subprocess

PROJECT_ID = "poc-tfm-tests"
REGION = "us-central1"
ENV_NAME = "tfm-composer-env"
DAG_NAME = "persistent_escalated_dag"

def run_cmd(cmd):
    print(f"[+] Running: {cmd}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print("[!] Error executing command.")
        exit(1)

def trigger_dag():
    print("[*] Triggering DAG manually to force execution …")
    run_cmd(
        f"gcloud composer environments run {ENV_NAME} "
        f"--location={REGION} --project={PROJECT_ID} "
        f"dags trigger -- {DAG_NAME}"
    )
    print("[✓] DAG manually triggered.")

if __name__ == "__main__":
    trigger_dag()
