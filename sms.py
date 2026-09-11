import urllib.request
import urllib.parse
import urllib.error
import json
import base64
import smtplib
import ssl
import config

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


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
    Send TRY-FIT OTP.

    Primary:
        Resend API

    Fallback:
        Gmail SMTP

    Gmail credentials are read only from environment variables
    through config.py.
    """

    subject = f"TRY-FIT Verification Code: {otp}"

    message_html = build_otp_html(otp)

    plain_message = f"""
TRY-FIT

Security Verification Code

Your TRY-FIT verification code is:

{otp}

This code is valid for 5 minutes.

If you did not request this code, please ignore this email.
Do not share this verification code with anyone.
"""

    # ============================================================
    # 1. TRY RESEND FIRST
    # ============================================================

    if config.RESEND_API_KEY:
        try:
            import requests

            url = "https://api.resend.com/emails"

            headers = {
                "Authorization": f"Bearer {config.RESEND_API_KEY}",
                "Content-Type": "application/json"
            }

            sender_email = getattr(
                config,
                "SENDER_EMAIL",
                "TRY-FIT <onboarding@resend.dev>"
            )

            data = {
                "from": sender_email,
                "to": [to_email],
                "subject": subject,
                "html": message_html
            }

            response = requests.post(
                url,
                headers=headers,
                json=data,
                timeout=15
            )

            if response.status_code in (200, 201):
                print(
                    f"[EMAIL OTP] Resend sent email successfully "
                    f"to {to_email}"
                )

                return (
                    True,
                    "Verification code sent to your email address."
                )

            # Resend rejected the request.
            # Do NOT expose the full Resend error to the user.
            print(
                f"[EMAIL OTP] Resend failed for {to_email}. "
                f"Status: {response.status_code}. "
                f"Trying Gmail SMTP fallback."
            )

        except Exception as e:
            print(
                f"[EMAIL OTP] Resend exception: {str(e)}. "
                f"Trying Gmail SMTP fallback."
            )

    else:
        print(
            "[EMAIL OTP] Resend API key is not configured. "
            "Trying Gmail SMTP fallback."
        )

    # ============================================================
    # 2. GMAIL SMTP FALLBACK
    # ============================================================

    gmail_user = getattr(config, "GMAIL_USER", "")
    gmail_password = getattr(config, "GMAIL_APP_PASSWORD", "")

    if not gmail_user:
        return False, "Email service is not configured."

    if not gmail_password:
        return False, "Email service is not configured."

    try:
        msg = MIMEMultipart("alternative")

        msg["From"] = gmail_user
        msg["To"] = to_email
        msg["Subject"] = subject

        msg.attach(
            MIMEText(
                plain_message,
                "plain",
                "utf-8"
            )
        )

        msg.attach(
            MIMEText(
                message_html,
                "html",
                "utf-8"
            )
        )

        context = ssl.create_default_context()

        with smtplib.SMTP(
            "smtp.gmail.com",
            587,
            timeout=20
        ) as server:

            server.ehlo()
            server.starttls(context=context)
            server.ehlo()

            server.login(
                gmail_user,
                gmail_password
            )

            server.sendmail(
                gmail_user,
                [to_email],
                msg.as_string()
            )

        print(
            f"[EMAIL OTP] Gmail SMTP sent email successfully "
            f"to {to_email}"
        )

        return (
            True,
            "Verification code sent to your email address."
        )

    except smtplib.SMTPAuthenticationError:
        print(
            "[EMAIL OTP] Gmail authentication failed. "
            "Check GMAIL_USER and GMAIL_APP_PASSWORD "
            "environment variables."
        )

        return (
            False,
            "Email service authentication failed."
        )

    except smtplib.SMTPException as e:
        print(
            f"[EMAIL OTP] Gmail SMTP error: {str(e)}"
        )

        return (
            False,
            "Email service is temporarily unavailable."
        )

    except Exception as e:
        print(
            f"[EMAIL OTP] Gmail connection error: {str(e)}"
        )

        return (
            False,
            "Email service is temporarily unavailable."
        )


def send_twilio_sms(to_number, otp):
    if not config.TWILIO_ACCOUNT_SID or config.TWILIO_ACCOUNT_SID == 'your_account_sid':
        return False, "Twilio Account SID is not configured in config.py"

    if not config.TWILIO_AUTH_TOKEN or config.TWILIO_AUTH_TOKEN == 'your_auth_token':
        return False, "Twilio Auth Token is not configured in config.py"

    if not config.TWILIO_FROM_NUMBER or config.TWILIO_FROM_NUMBER == 'your_twilio_number':
        return False, "Twilio From Number is not configured in config.py"

    url = f"https://api.twilio.com/2010-04-01/Accounts/{config.TWILIO_ACCOUNT_SID}/Messages.json"

    formatted_num = format_mobile_number(to_number)

    message_body = f"Your TRY-FIT verification code is: {otp}. Please do not share this OTP."

    data = urllib.parse.urlencode({
        'To': formatted_num,
        'From': config.TWILIO_FROM_NUMBER,
        'Body': message_body
    }).encode('utf-8')

    req = urllib.request.Request(url, data=data, method='POST')

    auth_str = f"{config.TWILIO_ACCOUNT_SID}:{config.TWILIO_AUTH_TOKEN}"
    auth_b64 = base64.b64encode(auth_str.encode('utf-8')).decode('utf-8')

    req.add_header('Authorization', f'Basic {auth_b64}')
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')

    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode('utf-8')
            res_json = json.loads(res_body)

            if response.status in (200, 201):
                return True, "Verification code sent to your mobile number via SMS."
            else:
                return False, f"Twilio API Error: {res_body}"

    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8')

        try:
            err_json = json.loads(err_body)
            return False, f"Twilio SMS Error: {err_json.get('message', err_body)}"
        except Exception:
            return False, f"Twilio SMS Error: {err_body}"

    except Exception as e:
        return False, f"Twilio Connection Error: {str(e)}"


def send_fast2sms_sms(to_number, otp):
    if not config.FAST2SMS_API_KEY:
        return False, "Fast2SMS API key is not configured in config.py"

    clean = ''.join(c for c in to_number if c.isdigit())

    if len(clean) >= 10:
        formatted_num = clean[-10:]
    else:
        return False, f"Invalid mobile number format: {to_number}"

    url = "https://www.fast2sms.com/dev/bulkV2"

    message_body = f"Your TRY-FIT verification code is {otp}"

    params = urllib.parse.urlencode({
        "authorization": config.FAST2SMS_API_KEY,
        "message": message_body,
        "language": "english",
        "route": "q",
        "numbers": formatted_num
    })

    full_url = f"{url}?{params}"

    req = urllib.request.Request(full_url, method='GET')
    req.add_header('cache-control', 'no-cache')

    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode('utf-8')
            res_json = json.loads(res_body)

            if res_json.get("return") is True:
                return True, "Verification code sent to your mobile number via Fast2SMS."
            else:
                return False, f"Fast2SMS API Error: {res_json.get('message', res_body)}"

    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8')

        try:
            err_json = json.loads(err_body)
            return False, f"{err_json.get('message', err_body)}"
        except Exception:
            return False, f"Fast2SMS Error: {err_body}"

    except Exception as e:
        return False, f"Fast2SMS Connection Error: {str(e)}"


def send_otp(recipient, otp, email_address=None):
    target_email = email_address if email_address else recipient

    if '@' in str(target_email):
        return send_gmail_otp(target_email, otp)

    provider = config.OTP_PROVIDER.lower().strip()

    if provider == 'gmail' or config.GMAIL_USER:
        return send_gmail_otp(target_email, otp)

    # Fallback log
    print("\n==========================================")
    print(f"[OTP LOG] Verification OTP for {recipient}: {otp}")
    print("==========================================\n")

    return True, f"Verification OTP: {otp}"