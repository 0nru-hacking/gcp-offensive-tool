from flask import Flask, request
import json

app = Flask(__name__)

@app.route('/', methods=['POST'])
def receive_event():
    print("[+] Incoming Firestore Trigger webhook received.")

    try:
        # Parsear cuerpo del POST
        data = request.get_json()
        print("[+] Raw POST body:")
        print(json.dumps(data, indent=4))

        # Verificar si hay cabecera de autorización (aunque no se use en este abuso)
        auth_header = request.headers.get("Authorization")
        print("[+] Authorization header:")
        print(auth_header if auth_header else "None")

    except Exception as e:
        print(f"[!] Error parsing request: {e}")

    return '', 204  # No Content

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
