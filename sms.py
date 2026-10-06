import smtplib
import socket
import urllib.request
import urllib.parse
import urllib.error
import json
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import config


def format_mobile_number(num):
    clean = ''.join(c for c in num if c.isdigit() or c == '+')

    if len(clean) == 10 and not clean.startswith('+'):
        return '+91' + clean

    if not clean.startswith('+') and len(clean) > 0:
        return '+' + clean

    return clean


def build_otp_html(otp):
    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #0a0a0f; color: #f9fafb; padding: 20px; text-align: center;">
        <div style="max-width: 480px; margin: 0 auto; background-color: #12121c; border: 1px solid rgba(255,255,255,0.06); border-radius: 16px; padding: 30px; box-shadow: 0 10px 25px rgba(0,0,0,0.5);">

            <div style="font-size: 24px; font-weight: bold; color: #fbbf24; margin-bottom: 20px; letter-spacing: -0.5px;">
                TRY-FIT
            </div>

            <div style="font-size: 18px; font-weight: bold; margin-bottom: 10px; color: #ffffff;">
                Security Verification Code
            </div>

            <p style="color: #9ca3af; font-size: 14px; line-height: 1.5; margin-bottom: 25px;">
                Please use the verification code below to complete your sign in or registration.
                This code is valid for 5 minutes.
            </p>

            <div style="background-color: rgba(245, 158, 11, 0.08); border: 1px dashed rgba(245, 158, 11, 0.3); border-radius: 12px; padding: 15px; font-size: 32px; font-weight: bold; color: #fbbf24; letter-spacing: 4px; margin-bottom: 25px;">
                {otp}
            </div>

            <p style="color: #6b7280; font-size: 12px; line-height: 1.4;">
                If you did not request this code, please ignore this email.
                Do not share this verification code with anyone.
            </p>

        </div>
    </body>
    </html>
    """


def send_gmail_otp(to_email, otp):
    """
    Send TRY-FIT OTP using Gmail SMTP.
    Uses smtplib.SMTP("smtp.gmail.com", 587) with STARTTLS.
    """
    gmail_user = getattr(config, 'GMAIL_USER', '').strip()
    raw_password = getattr(config, 'GMAIL_APP_PASSWORD', '').strip()
    clean_password = raw_password.replace(' ', '')

    # Check for missing or placeholder credentials
    if not gmail_user or not clean_password or 'your_email' in gmail_user.lower() or 'your-real' in gmail_user.lower() or 'your_app_password' in clean_password.lower():
        print("[EMAIL OTP] Gmail SMTP credentials missing or unconfigured in .env")
        return False, "Email service is not configured. Please set valid GMAIL_USER and GMAIL_APP_PASSWORD in .env."

    subject = "Your TRY-FIT Verification Code"

    # Plain-text body
    body_text = (
        "TRY-FIT\n\n"
        "Your verification code is:\n\n"
        f"{otp}\n\n"
        "This OTP will expire in 5 minutes.\n\n"
        "If you did not request this code, you can ignore this email. Do not share this verification code with anyone.\n"
    )

    # HTML body with branding
    body_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 20px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #0b0f19; color: #f3f4f6;">
        <div style="max-width: 480px; margin: 20px auto; background-color: #111827; border: 1px solid #1f2937; border-radius: 16px; padding: 32px; box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5); text-align: center;">
            <div style="font-size: 26px; font-weight: 800; color: #d97706; letter-spacing: 2px; margin-bottom: 8px;">
                TRY-FIT
            </div>
            <div style="font-size: 14px; text-transform: uppercase; letter-spacing: 1.5px; color: #9ca3af; margin-bottom: 24px;">
                Virtual Wardrobe & Fashion
            </div>
            <div style="font-size: 18px; font-weight: 600; color: #ffffff; margin-bottom: 12px;">
                Your Verification Code
            </div>
            <p style="color: #9ca3af; font-size: 14px; line-height: 1.6; margin: 0 0 24px 0;">
                Please use the verification code below to complete your authentication. This code is valid for <strong>5 minutes</strong>.
            </p>
            <div style="background-color: #1f2937; border: 1px dashed #d97706; border-radius: 12px; padding: 18px; font-size: 34px; font-weight: 800; color: #fbbf24; letter-spacing: 6px; font-family: monospace; margin-bottom: 24px;">
                {otp}
            </div>
            <p style="color: #6b7280; font-size: 12px; line-height: 1.5; margin: 0;">
                If you did not request this code, please ignore this email.<br>
                Do not share this verification code with anyone.
            </p>
        </div>
    </body>
    </html>
    """

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = f"TRY-FIT <{gmail_user}>"
    msg['To'] = to_email

    msg.attach(MIMEText(body_text, 'plain', 'utf-8'))
    msg.attach(MIMEText(body_html, 'html', 'utf-8'))

    # Resolve IPv4 to prevent IPv6 socket connection hangs on Windows
    smtp_host = "smtp.gmail.com"
    try:
        addr_info = socket.getaddrinfo("smtp.gmail.com", 587, socket.AF_INET, socket.SOCK_STREAM)
        if addr_info:
            smtp_host = addr_info[0][4][0]
    except Exception:
        smtp_host = "smtp.gmail.com"

    try:
        print(f"[EMAIL OTP] Connecting to Gmail SMTP (host={smtp_host}, port=587) ...")
        server = smtplib.SMTP(smtp_host, 587, timeout=15.0)
        server.ehlo()
        server.starttls()
        server.ehlo()
        print(f"[EMAIL OTP] Authenticating as {gmail_user} ...")
        server.login(gmail_user, clean_password)
        print(f"[EMAIL OTP] Sending email to {to_email} ...")
        server.sendmail(gmail_user, [to_email], msg.as_string())
        server.quit()
        print(f"[EMAIL OTP] Verification code sent successfully via Gmail SMTP to {to_email}")
        return True, "Verification code sent to your email address."

    except smtplib.SMTPAuthenticationError:
        print("[EMAIL OTP] Gmail SMTP authentication failed: Invalid username or App Password.")
        return False, "Gmail authentication failed. Please verify your Gmail App Password."

    except (smtplib.SMTPConnectError, socket.timeout, TimeoutError):
        print("[EMAIL OTP] Gmail SMTP connection timed out.")
        return False, "Unable to connect to Gmail SMTP server. Please check network."

    except smtplib.SMTPException as e:
        print(f"[EMAIL OTP] Gmail SMTP error: {type(e).__name__}")
        return False, "Failed to send verification code. Please try again."

    except Exception as e:
        print(f"[EMAIL OTP] Unexpected email error: {type(e).__name__}")
        return False, "Failed to send verification code. Please try again."


def send_twilio_sms(to_number, otp):
    if not config.TWILIO_ACCOUNT_SID or config.TWILIO_ACCOUNT_SID == 'your_account_sid':
        return False, "Twilio Account SID is not configured in config.py"

    if not config.TWILIO_AUTH_TOKEN or config.TWILIO_AUTH_TOKEN == 'your_auth_token':
        return False, "Twilio Auth Token is not configured in config.py"

    if not config.TWILIO_FROM_NUMBER or config.TWILIO_FROM_NUMBER == 'your_twilio_number':
        return False, "Twilio From Number is not configured in config.py"

    url = (
        f"https://api.twilio.com/2010-04-01/Accounts/"
        f"{config.TWILIO_ACCOUNT_SID}/Messages.json"
    )

    formatted_num = format_mobile_number(to_number)

    message_body = (
        f"Your TRY-FIT verification code is: {otp}. "
        f"Please do not share this OTP."
    )

    data = urllib.parse.urlencode({
        'To': formatted_num,
        'From': config.TWILIO_FROM_NUMBER,
        'Body': message_body
    }).encode('utf-8')

    req = urllib.request.Request(
        url,
        data=data,
        method='POST'
    )

    auth_str = (
        f"{config.TWILIO_ACCOUNT_SID}:"
        f"{config.TWILIO_AUTH_TOKEN}"
    )

    auth_b64 = base64.b64encode(
        auth_str.encode('utf-8')
    ).decode('utf-8')

    req.add_header(
        'Authorization',
        f'Basic {auth_b64}'
    )

    req.add_header(
        'Content-Type',
        'application/x-www-form-urlencoded'
    )

    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode('utf-8')
            res_json = json.loads(res_body)

            if response.status in (200, 201):
                return (
                    True,
                    "Verification code sent to your mobile number via SMS."
                )

            return False, f"Twilio API Error: {res_body}"

    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8')

        try:
            err_json = json.loads(err_body)

            return (
                False,
                f"Twilio SMS Error: "
                f"{err_json.get('message', err_body)}"
            )

        except Exception:
            return False, f"Twilio SMS Error: {err_body}"

    except Exception as e:
        return False, f"Twilio Connection Error: {str(e)}"


def send_fast2sms_sms(to_number, otp):
    if not config.FAST2SMS_API_KEY:
        return False, "Fast2SMS API key is not configured in config.py"

    clean = ''.join(
        c for c in to_number
        if c.isdigit()
    )

    if len(clean) >= 10:
        formatted_num = clean[-10:]
    else:
        return False, f"Invalid mobile number format: {to_number}"

    url = "https://www.fast2sms.com/dev/bulkV2"

    message_body = (
        f"Your TRY-FIT verification code is {otp}"
    )

    params = urllib.parse.urlencode({
        "authorization": config.FAST2SMS_API_KEY,
        "message": message_body,
        "language": "english",
        "route": "q",
        "numbers": formatted_num
    })

    full_url = f"{url}?{params}"

    req = urllib.request.Request(
        full_url,
        method='GET'
    )

    req.add_header(
        'cache-control',
        'no-cache'
    )

    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode('utf-8')
            res_json = json.loads(res_body)

            if res_json.get("return") is True:
                return (
                    True,
                    "Verification code sent to your mobile number via Fast2SMS."
                )

            return (
                False,
                f"Fast2SMS API Error: "
                f"{res_json.get('message', res_body)}"
            )

    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8')

        try:
            err_json = json.loads(err_body)

            return (
                False,
                f"{err_json.get('message', err_body)}"
            )

        except Exception:
            return False, f"Fast2SMS Error: {err_body}"

    except Exception as e:
        return False, f"Fast2SMS Connection Error: {str(e)}"


def send_otp(recipient, otp, email_address=None):
    target_email = (
        email_address
        if email_address
        else recipient
    )

    # Email OTP
    if '@' in str(target_email):
        return send_gmail_otp(
            target_email,
            otp
        )

    # SMS OTP
    provider = getattr(config, 'OTP_PROVIDER', '').lower().strip()

    if provider == 'twilio':
        return send_twilio_sms(recipient, otp)
    elif provider == 'fast2sms':
        return send_fast2sms_sms(recipient, otp)
    elif provider == 'gmail' or getattr(config, 'GMAIL_USER', ''):
        return send_gmail_otp(
            target_email,
            otp
        )

    print("[EMAIL OTP] No active email or SMS delivery service configured.")
    return False, "Email delivery service is not configured."