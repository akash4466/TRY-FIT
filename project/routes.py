import json
import urllib.parse
from otp import request_otp, verify_otp
from auth import signup_user, login_user, login_verify

def handle_api_request(handler):
    path = handler.path
    method = handler.command
    
    content_length = int(handler.headers.get('Content-Length', 0))
    body = {}
    if content_length > 0:
        try:
            raw_bytes = handler.rfile.read(content_length)
            decoded_str = raw_bytes.decode('utf-8')
            try:
                body = json.loads(decoded_str)
            except json.JSONDecodeError:
                parsed = urllib.parse.parse_qs(decoded_str)
                body = {k: v[0] if isinstance(v, list) and len(v) == 1 else v for k, v in parsed.items()}
        except UnicodeDecodeError:
            return {"success": False, "message": "Invalid request payload encoding."}, 400
        except Exception as e:
            return {"success": False, "message": "Failed to parse request body."}, 400

    if path == '/api/send-otp' and method == 'POST':
        email = body.get('email')
        if not email:
            return {"success": False, "message": "Field 'email' is required."}, 400
        return request_otp(str(email))

    elif path == '/api/verify-otp' and method == 'POST':
        email = body.get('email')
        otp_val = body.get('otp') or body.get('code')
        if not email or not otp_val:
            return {"success": False, "message": "Fields 'email' and 'otp' are required."}, 400
        return verify_otp(str(email), str(otp_val))

    elif path == '/api/signup' and method == 'POST':
        full_name = body.get('full_name') or body.get('name')
        email = body.get('email')
        return signup_user(full_name, email)

    elif path == '/api/login' and method == 'POST':
        email = body.get('email')
        otp_val = body.get('otp')
        if not email:
            return {"success": False, "message": "Field 'email' is required."}, 400
        if otp_val:
            return login_verify(str(email), str(otp_val))
        return login_user(str(email))

    return {"success": False, "message": "API endpoint not found"}, 404
