import subprocess

PROJECT_ID = "poc-tfm-tests"
ATTACKER_SA_NAME = "attacker-sa"
ATTACKER_SA_EMAIL = f"{ATTACKER_SA_NAME}@{PROJECT_ID}.iam.gserviceaccount.com"
KEY_FILE = "attacker-sa-key.json"

# Cuenta privilegiada
SUPPORT_SA_EMAIL = "internal-support@poc-tfm-tests.iam.gserviceaccount.com"
SUPPORT_SA_KEY = "internal-support-key.json"

def run_cmd(cmd):
    print(f"[+] Running: {cmd}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print("[!] Error executing command.")
        exit(1)

def authenticate_support_account():
    print("[*] Switching back to privileged service account...")
    run_cmd(f"gcloud auth activate-service-account {SUPPORT_SA_EMAIL} --key-file={SUPPORT_SA_KEY}")
    print("[✓] Authenticated as privileged service account.")

def delete_service_account():
    print("[*] Deleting attacker service account...")
    run_cmd(f"gcloud iam service-accounts delete {ATTACKER_SA_EMAIL} --quiet --project={PROJECT_ID}")
    print("[✓] Service account deleted.")

def delete_key_file():
    print("[*] Deleting local key file...")
    run_cmd(f"rm -f {KEY_FILE}")
    print("[✓] Key file deleted.")

def main():
    authenticate_support_account()
    delete_service_account()
    delete_key_file()

if __name__ == "__main__":
    main()
