<p align="center">
  <img src="banner.png" alt="gcp-offensive-tool" width="100%">
</p>

---

# CLOUD TFM TOOL

This repository contains a **modular offensive security tool** developed as part of a Master's Thesis in Cybersecurity.  
It enables the **creation and exploitation of vulnerable configurations** in Google Cloud Platform (GCP), simulating realistic **post-compromise scenarios** such as privilege escalation, identity abuse, and persistence.

---

## 🔍 Purpose

The tool simulates **realistic offensive scenarios in GCP** by:
- Creating vulnerable environments (overprivileged or misconfigured service accounts).
- Abusing **Cloud Tasks** for privilege escalation and deferred persistence.
- Deploying **malicious Firestore triggers** for code execution and persistence.
- Uploading **malicious DAGs in Cloud Composer** for privilege escalation and secret access.
- Simulating **external payload execution via obfuscated DAGs** to exfiltrate secrets and maintain persistence.
- Demonstrating **token replay attacks** against private endpoints.

---

## ⚠️ Important Notice (Costs & Security)

- Some resources incur costs (e.g., Cloud Composer, Cloud Run, network egress, invocations). Always use a disposable project and configure budget alerts.
  
- Run the tool only in projects you own and with proper authorization. It is intended for educational/research purposes in isolated environments.

- Many scripts assume `PROJECT_ID=poc-tfm-tests`. If you use a different project, update it in `run_attack.py` and/or within the `modules/` scripts.

---

## 📁 Structure

The tool is organized into modular components:

- **`core/`**  
  Common reusable functions (e.g., OIDC token generation, authentication helpers).

- **`modules/`**  
  Contains offensive modules for each abuse:
  - `abuse_cloud_tasks/`
  - `abuse_firestore_trigger/`
  - `abuse_composer_dag/`
  - `abuse_composer_external_payload/`

- **`cloudrun_api/`**  
  Simple Dockerized Cloud Run backend used to demonstrate token replay attacks.

- **`run_attack.py`**  
  Master entrypoint. Coordinates abuse modules and executes complete attack chains.

- **`requirements.txt`**  
  Python dependencies.

- **`README.md`**, **`LICENSE`**, **`.gitignore`**  
  Documentation and licensing.

---

## 🛠️ Implemented Abuses

### 1️⃣ Cloud Tasks – Privileged Service Account Execution
- Deploys a Cloud Task running as a **privileged service account**.
- Extracts a valid **OIDC token**.
- Replays the token to access a **private Cloud Run service**.

---

### 2️⃣ Firestore – Malicious Trigger for Persistence & Code Execution
- Deploys a **malicious Cloud Function** triggered by Firestore document writes.
- Executes attacker-controlled payloads (e.g., POST to external webhook).
- Persists execution **even after attacker account deletion**.

---

### 3️⃣ Cloud Composer – Persistent DAG Abuse with Escalated Privileges
- Uploads a **malicious DAG** into Composer’s DAG bucket.
- DAG executes under **Composer’s Service Account**, often with elevated privileges.
- Demonstrates access to **sensitive services like Secret Manager**.

---

### 4️⃣ Cloud Composer – External Payload Execution via Obfuscated DAG
- DAG fetches and executes an **external payload** from a Signed URL.
- Payload dynamically rotates, evading static review.
- Enables **secret exfiltration, privilege escalation, and persistence**.

---

## ⚙️ Requirements

- Python 3.8+
- Google Cloud SDK (`gcloud`) installed and authenticated
- A GCP project with the following APIs enabled:
  - `cloudtasks.googleapis.com`
  - `run.googleapis.com`
  - `firestore.googleapis.com`
  - `cloudfunctions.googleapis.com`
  - `composer.googleapis.com`
  - `secretmanager.googleapis.com`

---

## 📦 Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/onru-hacking/gcp-offensive-tool.git
cd gcp-offensive-tool
pip install -r requirements.txt
```

If the install of requirements fails:

### Create and activate a virtual environment (recommended)

```bash
# Create environment
python3 -m venv venv

# Activate environment (Linux/MacOS)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## 🔧 Installing Google Cloud SDK (Linux)

The tool requires the Google Cloud SDK (`gcloud`) to perform authentication (`gcloud auth login`).  
Follow these steps to install it on Debian/Ubuntu/Kali:

```bash
# 1) Create the keyring and import the Google signing key
sudo mkdir -p /usr/share/keyrings
curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg \
  | sudo gpg --dearmor -o /usr/share/keyrings/google-cloud-sdk-archive-keyring.gpg
```

```bash
# 2) Add the Google Cloud SDK repository
echo "deb [signed-by=/usr/share/keyrings/google-cloud-sdk-archive-keyring.gpg] https://packages.cloud.google.com/apt cloud-sdk main" \
  | sudo tee /etc/apt/sources.list.d/google-cloud-sdk.list
```

```bash
# 3) Update package lists and install the SDK
sudo apt-get update
sudo apt-get install -y google-cloud-sdk
```

```bash
# 4) Verify installation
gcloud --version
```

## 🔑 Google Cloud Authentication

Before running the tool, authenticate with your Google Cloud account using the CLI:

```bash
gcloud auth login
gcloud config set project <YOUR_PROJECT_ID>
```

Make sure the selected project has billing enabled and the required APIs activated (the tool will notify you if any are missing).

---

## 🌐 ngrok Configuration

1. Install ngrok and log in with your authtoken:

```bash
ngrok config add-authtoken <YOUR_AUTHTOKEN>
```

2. The tool will automatically start a listener when the PoC requires it.


---

## 🔑 Prerequisite: Service Account Setup

Before running any abuse module, you must create a privileged Service Account (Owner role) and download its authentication key. This account is required by the tool to authenticate against GCP APIs.

1. **Create the Service Account (with Owner role):**

```bash
gcloud iam service-accounts create internal-support \
    --description="Privileged SA for TFM offensive tool" \
    --display-name="Internal Support SA"

```

2. Bind Owner role to the Service Account:

```bash
gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="serviceAccount:internal-support@PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/owner"
```

3. Generate and download the JSON key:

```bash
gcloud iam service-accounts keys create internal-support-key.json \
    --iam-account=internal-support@PROJECT_ID.iam.gserviceaccount.com
```

---

## 🚀 Example Usage

### Abuse 1 – Cloud Tasks Privileged Execution

```bash
python3 run_attack.py --abuse cloud_tasks
```

### Abuse 2 – Firestore Malicious Trigger

```bash
python3 run_attack.py --abuse firestore_trigger
```

### Abuse 3 – Cloud Composer DAG Abuse

#### Full mode (creates a new Composer environment)

```bash
python3 run_attack.py --abuse composer_dag
```

#### Reuse existing Composer environment (If you already have a Composer environment deployed, you can skip environment creation and directly upload/execute the malicious DAG)

```bash
python3 run_attack.py --module composer_dag --use-existing <Name of the composer environment>
```

### Abuse 4 – Cloud Composer External Payload Execution

#### Full mode (creates a new Composer environment)

```bash
python3 run_attack.py --abuse composer_external_payload
```

#### Reuse existing Composer environment (If you already have a Composer environment deployed, you can skip environment creation and directly upload/execute the malicious DAG)

```bash
python3 run_attack.py --module composer_external_payload --use-existing <Name of the composer environment>
```




