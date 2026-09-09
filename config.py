import os

# Database configurations
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_USER = os.environ.get('DB_USER', 'root')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
DB_NAME = os.environ.get('DB_NAME', 'try-fit')

# Web Server configurations
PORT = int(os.environ.get('PORT', 8000))

# OTP Delivery settings
# Options: 'auto', 'fast2sms', 'twilio', 'gmail', 'dev'
OTP_PROVIDER = 'gmail'

# Gmail SMTP settings (used when OTP_PROVIDER = 'gmail')
GMAIL_USER = 'tryfit.project@gmail.com' # Your Gmail address
GMAIL_APP_PASSWORD = 'uuka qfph tiyq ctsg' # Your Gmail App password

# Twilio credentials
TWILIO_ACCOUNT_SID = 'your_account_sid'
TWILIO_AUTH_TOKEN = 'your_auth_token'
TWILIO_FROM_NUMBER = 'your_twilio_number'

# Fast2SMS credentials
FAST2SMS_API_KEY = ''
