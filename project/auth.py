from utils import is_valid_email, generate_jwt_token
from models import UserModel, OTPModel
from otp import request_otp, verify_otp

def signup_user(full_name: str, email: str) -> tuple[dict, int]:
    """
    Handles user signup.
    Requirements:
    - Full Name, Email inputs.
    - Validates email formats.
    - Ensures email is verified via OTP prior to account creation.
    - Prevents duplicate email registration.
    - Returns JWT auth token upon successful registration.
    """
    full_name = str(full_name or '').strip()
    email = str(email or '').strip().lower()

    if not full_name:
        return {"success": False, "message": "Full Name is required."}, 400

    if not is_valid_email(email):
        return {"success": False, "message": "Please enter a valid email address."}, 400

    # 1. Check if email is already registered
    existing_user = UserModel.get_by_email(email)
    if existing_user:
        return {
            "success": False,
            "message": "This email is already registered. Please log in."
        }, 400

    # 2. Check if email has verified OTP status
    if not OTPModel.is_email_verified(email):
        return {
            "success": False,
            "message": "Email is not verified. Please complete OTP verification first."
        }, 400

    # 3. Create user in database
    try:
        user_id = UserModel.create(full_name, email)
    except Exception as e:
        return {
            "success": False,
            "message": f"Database error during user registration: {str(e)}"
        }, 500

    # 4. Clean up verified OTP record after successful account creation
    OTPModel.invalidate_all_active_otps(email)

    # 5. Issue JWT Token
    token = generate_jwt_token(user_id, email, full_name)

    return {
        "success": True,
        "message": "User registered successfully",
        "user": {
            "id": user_id,
            "full_name": full_name,
            "email": email
        },
        "token": token
    }, 201


def login_user(email: str) -> tuple[dict, int]:
    """
    Initiates email login by sending OTP to registered email address.
    """
    if not is_valid_email(email):
        return {"success": False, "message": "Invalid email address format."}, 400

    email = str(email).strip().lower()

    # Check if user exists
    user = UserModel.get_by_email(email)
    if not user:
        return {
            "success": False,
            "message": "Email address is not registered. Please sign up first."
        }, 404

    # Trigger OTP request
    res, status_code = request_otp(email)
    if status_code in (200, 201):
        res["message"] = "Login OTP sent successfully"
    return res, status_code


def login_verify(email: str, raw_otp: str) -> tuple[dict, int]:
    """
    Verifies login OTP and returns JWT token.
    """
    if not is_valid_email(email):
        return {"success": False, "message": "Invalid email address format."}, 400

    email = str(email).strip().lower()

    # 1. Fetch user
    user = UserModel.get_by_email(email)
    if not user:
        return {
            "success": False,
            "message": "Email address is not registered."
        }, 404

    # 2. Verify OTP
    otp_res, status_code = verify_otp(email, raw_otp)
    if not otp_res.get("success"):
        return otp_res, status_code

    # 3. Clean up OTP record
    OTPModel.invalidate_all_active_otps(email)

    # 4. Issue JWT Token
    token = generate_jwt_token(user["id"], user["email"], user["full_name"])

    return {
        "success": True,
        "message": "Login successful",
        "user": {
            "id": user["id"],
            "full_name": user["full_name"],
            "email": user["email"]
        },
        "token": token
    }, 200
