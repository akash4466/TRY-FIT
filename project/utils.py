import re
import hmac
import hashlib
import datetime
import jwt
from config import config

def is_valid_email(email: str) -> bool:
    """Validates standard email address format."""
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, str(email).strip()))

def hash_otp(raw_otp: str) -> str:
    """Hashes raw OTP using HMAC-SHA256 with server SECRET_KEY (never stored in plain text)."""
    key = config.SECRET_KEY.encode('utf-8')
    msg = str(raw_otp).encode('utf-8')
    return hmac.new(key, msg, hashlib.sha256).hexdigest()

def verify_otp_hash(raw_otp: str, stored_hash: str) -> bool:
    """Secure constant-time comparison to prevent timing attacks."""
    calculated_hash = hash_otp(raw_otp)
    return hmac.compare_digest(calculated_hash, stored_hash)

def generate_jwt_token(user_id: int, email: str, full_name: str) -> str:
    """Generates JWT authentication token for logged-in user."""
    payload = {
        'user_id': user_id,
        'email': email,
        'full_name': full_name,
        'iat': datetime.datetime.utcnow(),
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=config.JWT_EXPIRES_MINUTES)
    }
    return jwt.encode(payload, config.SECRET_KEY, algorithm='HS256')

def decode_jwt_token(token: str) -> dict:
    """Decodes and validates JWT token."""
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=['HS256'])
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None
