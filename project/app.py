import http.server
import socketserver
import json
from config import config
from database import init_db
from routes import handle_api_request

class ReusableTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True

class PurePythonAPIHandler(http.server.BaseHTTPRequestHandler):

    def send_json_response(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        if self.path == '/health':
            self.send_json_response({
                "status": "healthy",
                "service": "OTP Authentication API (Pure Python)",
                "email_provider": getattr(config, 'EMAIL_PROVIDER', 'console')
            }, 200)
        else:
            self.send_json_response({"success": False, "message": "API endpoint not found"}, 404)

    def do_POST(self):
        try:
            response_data, status_code = handle_api_request(self)
            self.send_json_response(response_data, status_code)
        except Exception as e:
            print(f"[Server Error] POST Handler Exception: {e}")
            self.send_json_response({"success": False, "message": "Internal Server Error"}, 500)

def run_server():
    init_db()
    port = getattr(config, 'PORT', 5000)
    server_address = ('0.0.0.0', port)
    httpd = ReusableTCPServer(server_address, PurePythonAPIHandler)
    print(f"[Server] OTP Authentication API Server running on port {port} using Pure Python http.server")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        httpd.server_close()

if __name__ == '__main__':
    run_server()
