import subprocess, sys, time

PROJECT_ID="poc-tfm-tests"
REGION="us-central1"
ENV_NAME="tfm-composer-env"
DAG_NAME="persistent_escalated_dag"
OWNER_SA="internal-support@poc-tfm-tests.iam.gserviceaccount.com"
OWNER_KEY="internal-support-key.json"

def run(args, check=True, capture=False):
    if isinstance(args, str):
        print(f"[+] Running: {args}")
        r = subprocess.run(args, shell=True,
                           stdout=subprocess.PIPE if capture else None,
                           stderr=subprocess.PIPE if capture else None,
                           text=True)
    else:
        print(f"[+] Running: {' '.join(args)}")
        r = subprocess.run(args,
                           stdout=subprocess.PIPE if capture else None,
                           stderr=subprocess.PIPE if capture else None,
                           text=True)
    if check and r.returncode != 0:
        if capture:
            print(r.stderr or "")
        print("[!] Error executing command.")
        sys.exit(1)
    return r

def auth_owner():
    print("[*] Authenticating as privileged SA …")
    run(["gcloud","auth","activate-service-account",OWNER_SA,
         "--key-file",OWNER_KEY,f"--project={PROJECT_ID}"])
    print("[✓] Authenticated.")

def composer_run(cmd_args, attempts=30, sleep=10, check=True):
    full=["gcloud","composer","environments","run",ENV_NAME,
          f"--location={REGION}",f"--project={PROJECT_ID}",*cmd_args]
    for left in range(attempts,0,-1):
        r=subprocess.run(full)
        if r.returncode==0: return True
        if left>1:
            print(f"[i] Webserver not ready for: {' '.join(cmd_args[:2])}. "
                  f"Retrying in {sleep}s… ({left-1} left)")
            time.sleep(sleep)
    if check:
        print("[!] Command failed persistently. Aborting."); sys.exit(1)
    return False

def wait_dag_visible(timeout=240, poll=6):
    print("[*] Waiting for DAG to be visible in Airflow…")
    start=time.time()
    while time.time()-start<timeout:
        r=run(["gcloud","composer","environments","run",ENV_NAME,
               f"--location={REGION}",f"--project={PROJECT_ID}",
               "dags","list","--"],check=False,capture=True)
        if r.returncode==0 and DAG_NAME in (r.stdout or ""):
            print("[✓] DAG is visible."); return True
        time.sleep(poll)
    print("[i] DAG not visible yet; proceeding anyway."); return False

def unpause_and_trigger():
    print("[*] Unpausing DAG (idempotent)…")
    composer_run(["dags","unpause","--",DAG_NAME],attempts=10,sleep=6,check=False)
    print("[*] Triggering DAG manually…")
    composer_run(["dags","trigger","--",DAG_NAME],attempts=30,sleep=10,check=True)
    print("[✓] DAG manually triggered.")

def list_tasks():
    print("[*] Listing tasks…")
    composer_run(["tasks","list","--",DAG_NAME],attempts=6,sleep=5,check=False)

if __name__=="__main__":
    auth_owner()
    wait_dag_visible()
    unpause_and_trigger()
    list_tasks()
