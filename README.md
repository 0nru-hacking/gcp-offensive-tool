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

### 1. Deploy a vulnerable Cloud Task with OIDC impersonation

```bash
python3 abuse_cloud_tasks_token_privesc/create_vuln_env.py
```

2. Extract and display OIDC token for the overprivileged service account

```bash
python3 abuse_cloud_tasks_token_prives/exploit_token.py
```

3. Use the token to invoke a private Cloud Run endpoint

```bash
python3 abuse_cloud_tasks_token_privesc/trigger_run.py
```

4. Clean up all created resources

```bash
python3 abuse_cloud_tasks_token_privesc/cleanup.py
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


