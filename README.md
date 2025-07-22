# gcp-offensive-tool

This tool was developed as part of a Master's Thesis in Cybersecurity. It automates the creation of vulnerable configurations and the execution of real-world abuse techniques in Google Cloud Platform (GCP), allowing controlled testing of privilege escalation, persistence, and post-exploitation scenarios.

## 🔍 Purpose

The tool simulates realistic offensive security scenarios in GCP by:
- Creating vulnerable environments (e.g., overprivileged service accounts)
- Deploying offensive tasks and delayed executions
- Generating impersonation tokens (OIDC) for identity abuse
- Invoking private endpoints with replayed tokens
- Testing persistence and privilege escalation chains

## 📁 Structure

gcp-offensive-tool/
├── core/
│   └── auth_utils.py                   # Common functions (e.g., token creation)
├── abuse_cloud_tasks_token_privesc/
│   ├── create_vuln_env.py             # Deploys the vulnerable setup
│   ├── exploit_token.py               # Extracts and prints OIDC token
│   ├── trigger_run.py                 # Sends token to target endpoint
│   └── cleanup.py                     # Destroys the environment
├── requirements.txt
├── README.md
└── LICENSE


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

## ⚙️ Requirements

- Python 3.8+

- Google Cloud SDK (gcloud) installed and authenticated

- GCP project with Cloud Tasks and Cloud Run APIs enabled

## 📘 Related Work

This tool was inspired by:

    Offensive research on GCP privilege escalation

    Manual enumeration of identity bindings

    PurplePanda and BloodHound-style visualizations (WIP)

⚠️ Disclaimer

This tool is intended only for educational and research purposes within authorized environments. Do not use it against systems or services you do not own or have explicit permission to test.
📄 License

Distributed under the MIT License. See LICENSE for more information.


