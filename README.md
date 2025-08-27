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

### 0. Create and activate a virtual environment (recommended)

```bash
# Create environment
python3 -m venv venv

# Activate environment (Linux/MacOS)
source venv/bin/activate

# Activate environment (Windows PowerShell)
venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
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





