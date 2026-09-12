import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Production Application Configuration Loaded from Environment Variables"""
    
    # App Settings
    PORT = int(os.getenv('PORT', 5000))
    DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')
    SECRET_KEY = os.getenv('SECRET_KEY', 'default_fallback_secret_key_change_in_prod')
    JWT_EXPIRES_MINUTES = int(os.getenv('JWT_EXPIRES_MINUTES', 1440))
    # Razorpay credentials (test credentials should be set via .env)
    RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID')
    RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET')
    
    # Database Settings
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'try-fit')
    
    # OTP Rules & Security Policy
    OTP_EXPIRY_MINUTES = int(os.getenv('OTP_EXPIRY_MINUTES', 5))
    OTP_COOLDOWN_SECONDS = int(os.getenv('OTP_COOLDOWN_SECONDS', 30))
    OTP_MAX_ATTEMPTS = int(os.getenv('OTP_MAX_ATTEMPTS', 5))
    
    # Email / Resend / SMTP Configuration
    RESEND_API_KEY = os.getenv('RESEND_API_KEY', '')
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
    SENDER_EMAIL = os.getenv('SENDER_EMAIL', 'TRY-FIT <onboarding@resend.dev>' if RESEND_API_KEY else SMTP_USERNAME)
    
    # Provider selection: resend > smtp > console
    if RESEND_API_KEY:
        EMAIL_PROVIDER = os.getenv('EMAIL_PROVIDER', 'resend')
    elif SMTP_USERNAME:
        EMAIL_PROVIDER = os.getenv('EMAIL_PROVIDER', 'smtp')
    else:
        EMAIL_PROVIDER = 'console'

config = Config()
