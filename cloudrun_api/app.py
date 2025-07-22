from flask import Flask, request, jsonify
import os

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return jsonify({"message": "Private Cloud Run API - TFM Demo"})

@app.route("/secret", methods=["GET"])
def secret():
    auth_header = request.headers.get("Authorization", "")
    if "Bearer" not in auth_header:
        return jsonify({"error": "Missing Bearer token"}), 403
    
    # Aquí simulas que cualquiera con un token válido puede acceder
    return jsonify({
        "flag": os.environ.get("FLAG"),
        "api_key": os.environ.get("SECRET_KEY"),
        "note": "This data should be protected by IAM permissions"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
