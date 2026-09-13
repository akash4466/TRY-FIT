import os
from dotenv import load_dotenv

load_dotenv()

# Application mode & security
DEBUG = os.environ.get('DEBUG', '0').strip().lower() in ('1', 'true', 'yes', 'on')

_secret_key = os.environ.get('SECRET_KEY')
if not DEBUG and not _secret_key:
    raise RuntimeError('SECRET_KEY environment variable is required in production')
SECRET_KEY = _secret_key or 'tryfit_dev_fallback_secret_key_insecure'

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")

# Database configurations
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = int(os.environ.get('DB_PORT', 3306))
DB_USER = os.environ.get('DB_USER', 'root')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
DB_NAME = os.environ.get('DB_NAME', 'try-fit')

# Web Server configurations
PORT = int(os.environ.get('PORT', 8000))

# Razorpay Payment Gateway
RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID', '')
RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', '')

# OTP Delivery settings
GMAIL_USER = os.environ.get('GMAIL_USER', '')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')
RESEND_API_KEY = os.environ.get('RESEND_API_KEY', '')

BREVO_API_KEY = os.environ.get('BREVO_API_KEY', '')
BREVO_SENDER_EMAIL = os.environ.get('BREVO_SENDER_EMAIL', '')
BREVO_SENDER_NAME = os.environ.get('BREVO_SENDER_NAME', 'TRY-FIT')

# Email service
EMAIL_PROVIDER = os.environ.get('EMAIL_PROVIDER', 'resend')
SENDER_EMAIL = os.environ.get(
    'SENDER_EMAIL',
    'TRY-FIT <onboarding@resend.dev>'
)