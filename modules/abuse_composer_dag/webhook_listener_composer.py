from flask import Flask, request
import logging
import datetime

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.route('/', methods=['POST', 'GET'])
def handle_request():
    now = datetime.datetime.now().isoformat()
    print(f"\n[📥] Incoming request at {now}")
    
    print("[🌐] Request Metadata:")
    print(f"  - Remote IP: {request.remote_addr}")
    print(f"  - Method: {request.method}")
    print(f"  - Headers: {dict(request.headers)}")

    if request.is_json:
        data = request.get_json()
        print("[📦] JSON Payload Received:")
        for key, value in data.items():
            print(f"  - {key}: {value}")
    else:
        print("[⚠️] Non-JSON content received:")
        print(request.data.decode('utf-8'))

    return "✅ Listener received the Composer payload.", 200

if __name__ == '__main__':
    print("[*] Composer webhook listener is running on port 8080...")
    app.run(host='0.0.0.0', port=8080)
