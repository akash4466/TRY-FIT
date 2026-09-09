import secrets
import datetime
from config import config
from utils import is_valid_email, hash_otp, verify_otp_hash
from models import OTPModel
from email_service import send_email

def generate_random_6_digit_otp() -> str:
    """Generates a cryptographically secure 6-digit OTP code."""
    return f"{secrets.randbelow(900000) + 100000}"

def request_otp(email: str) -> tuple[dict, int]:
    """
    Handles OTP generation and dispatch via Email.
    Enforces:
    1. Email format validation.
    2. Rate limiting / Cooldown of 30 seconds between requests.
    3. Invalidation of previous active OTPs (only 1 active OTP per email).
    4. Secure HMAC-SHA256 hashing before storing.
    5. 5-minute expiry.
    """
    if not is_valid_email(email):
        return {
            "success": False,
            "message": "Invalid email address."
        }, 400

    email = str(email).strip().lower()
    now = datetime.datetime.now()

    # 1. Rate Limiting Check (1 request every 30 seconds)
    latest_otp = OTPModel.get_latest_active_otp(email)
    if latest_otp:
        time_since_creation = (now - latest_otp['created_at']).total_seconds()
        if time_since_creation < config.OTP_COOLDOWN_SECONDS:
            remaining_cooldown = int(config.OTP_COOLDOWN_SECONDS - time_since_creation)
            return {
                "success": False,
                "message": f"Please wait {remaining_cooldown} seconds before requesting a new OTP."
            }, 429

    # 2. Invalidate old active OTPs (Ensures only 1 active OTP per email)
    OTPModel.invalidate_all_active_otps(email)

    # 3. Generate 6-digit OTP code and hash it
    raw_otp = generate_random_6_digit_otp()
    hashed_otp = hash_otp(raw_otp)
    expires_at = now + datetime.timedelta(minutes=config.OTP_EXPIRY_MINUTES)

    # 4. Save to Database
    OTPModel.create_otp(email, hashed_otp, expires_at)

    # 5. Dispatch via Email Provider
    message_text = f"Your verification OTP code is: {raw_otp}. Valid for {config.OTP_EXPIRY_MINUTES} minutes. Do not share with anyone."
    subject = "Your Verification OTP"
    email_success, email_msg = send_email(email, subject, message_text)

    return {
        "success": True,
        "message": "OTP sent successfully",
        "otp_debug": raw_otp if config.DEBUG else None  # Include in debug output for easy API testing
    }, 200


def verify_otp(email: str, raw_otp: str) -> tuple[dict, int]:
    """
    Handles OTP verification.
    Enforces:
    1. 6-digit numeric OTP validation.
    2. Expiration check (5 minutes).
    3. Maximum 5 verification attempts security limit.
    4. Secure hash matching.
    5. Invalidation upon successful verification.
    """
    if not is_valid_email(email):
        return {
            "success": False,
            "message": "Invalid email address."
        }, 400

    if not raw_otp or not str(raw_otp).isdigit() or len(str(raw_otp)) != 6:
        return {
            "success": False,
            "message": "OTP must be a valid 6-digit number."
        }, 400

    email = str(email).strip().lower()
    raw_otp = str(raw_otp).strip()
    now = datetime.datetime.now()

    # 1. Fetch latest active OTP
    record = OTPModel.get_latest_active_otp(email)
    if not record:
        return {
            "success": False,
            "message": "No active OTP found for this email address. Please request a new code."
        }, 400

    # 2. Check Expiration (5 minutes)
    if record['expires_at'] < now:
        OTPModel.invalidate_all_active_otps(email)
        return {
            "success": False,
            "message": "OTP has expired. Please request a new verification code."
        }, 400

    # 3. Check Maximum Attempts Limit (5 attempts max)
    if record['attempts'] >= config.OTP_MAX_ATTEMPTS:
        OTPModel.invalidate_all_active_otps(email)
        return {
            "success": False,
            "message": "Maximum verification attempts exceeded. Please request a new OTP."
        }, 429

    # Increment attempt count in DB
    OTPModel.increment_attempts(record['id'])
    current_attempts = record['attempts'] + 1

    # 4. Constant-time Hash Comparison
    if not verify_otp_hash(raw_otp, record['otp_hash']):
        remaining = config.OTP_MAX_ATTEMPTS - current_attempts
        if remaining <= 0:
            OTPModel.invalidate_all_active_otps(email)
            return {
                "success": False,
                "message": "Incorrect OTP. Maximum attempts reached. Please request a new OTP."
            }, 400
        return {
            "success": False,
            "message": f"Incorrect OTP. {remaining} attempt(s) remaining."
        }, 400

    # 5. Success! Mark verified and invalidate/delete OTP record
    OTPModel.mark_verified(record['id'])

    return {
        "success": True,
        "message": "OTP verified"
    }, 200
