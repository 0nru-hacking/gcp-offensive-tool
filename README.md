<p align="center">
  <img src="banner.png" alt="gcp-offensive-tool" width="100%">
</p>

---

This repository contains a modular tool developed as part of a Master's Thesis in Cybersecurity. It enables the creation and exploitation of vulnerable configurations in Google Cloud Platform (GCP), simulating realistic post-compromise scenarios such as privilege escalation, identity abuse, and persistence.

---

## 🔍 Purpose

The tool simulates realistic offensive security scenarios in GCP by:
- Creating vulnerable environments (e.g., overprivileged service accounts)
- Deploying offensive tasks and delayed executions
- Generating impersonation tokens (OIDC) for identity abuse
- Invoking private endpoints with replayed tokens
- Testing persistence and privilege escalation chains

---

## 📁 Structure

The tool is organized into modular components:

- **`core/`**  
  Contains reusable utility functions such as OIDC token generation and authentication helpers.

- **`modules/`**  
  Reserved for offensive modules (Cloud Tasks and Firestore abuse, Spanner persistence). Currently under development.

- **`cloudrun_api/`**  
  Includes a simple Dockerized Cloud Run backend to receive replayed tokens (for exploitation demonstration).

- **`run_attack.py`**  
  Master entrypoint. Coordinates abuse modules and simulates complete attack chains.

- **`requirements.txt`**  
  List of Python dependencies.

- **`README.md`**, **`LICENSE`**, **`.gitignore`**  
  Project documentation and licensing information.


---

## 🚀 Example Usage

### 1. Run the full attack chain from the main entrypoint

```bash
PYTHONPATH=. python3 run_attack.py
```

This will:

- Deploy a vulnerable Cloud Task impersonating a high-privileged service account

- Extract a valid OIDC token

- Replay the token to invoke a private Cloud Run endpoint

- Clean up all created resources

---

🛠️ Optional: Run each step manually (for educational purposes)

You can also run individual steps to better understand the attack chain:

```bash
python3 modules/abuse_cloud_tasks/1_create_vulnerable_env.py
```

```bash
python3 modules/abuse_cloud_tasks/2_execute_attack.py
```

```bash
python3 modules/abuse_cloud_tasks/3_trigger_damage.py
```

```bash
python3 modules/abuse_cloud_tasks/4_cleanup.py
```

---

## ⚙️ Requirements

- Python 3.8+

- Google Cloud SDK (gcloud) installed and authenticated

- GCP project with Cloud Tasks and Cloud Run APIs enabled

---

## Instalation

Clone and install dependencies:

```bash
git clone https://github.com/onru-hacking/gcp-offensive-tool.git
cd gcp-offensive-tool
pip install -r requirements.txt
```

---

## 🎥 Demo

Coming soon! A short video will demonstrate a full abuse chain using Cloud Tasks, OIDC impersonation, and private Cloud Run endpoint invocation.

---

🧠 Thesis Context

This tool is part of a research thesis focused on offensive cloud security in Google Cloud Platform. It automates complex abuse chains typically executed manually, and facilitates:

    Controlled security research

    Defensive validation and alerting tests

    Enumeration of misconfigured privileges and identities

---

⚠️ Disclaimer

This tool is intended only for educational and research purposes within authorized environments. Do not use it against systems or services you do not own or have explicit permission to test.
📄 License

Distributed under the MIT License. See LICENSE for more information.


