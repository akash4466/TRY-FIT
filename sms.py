import urllib.request
import urllib.parse
import urllib.error
import json
import base64
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
    Send TRY-FIT OTP using Brevo HTTP API.

    The function name is kept as send_gmail_otp()
    so existing server.py does not need to change.
    """

    if not config.BREVO_API_KEY:
        print("[EMAIL OTP] Brevo API key is not configured.")
        return False, "Email service is not configured."

    sender_email = getattr(
        config,
        "BREVO_SENDER_EMAIL",
        ""
    )

    sender_name = getattr(
        config,
        "BREVO_SENDER_NAME",
        "TRY-FIT"
    )

    if not sender_email:
        print("[EMAIL OTP] Brevo sender email is not configured.")
        return False, "Email service is not configured."

    subject = f"TRY-FIT Verification Code: {otp}"

    message_html = build_otp_html(otp)

    try:
        import requests

        url = "https://api.brevo.com/v3/smtp/email"

        headers = {
            "accept": "application/json",
            "api-key": config.BREVO_API_KEY,
            "content-type": "application/json"
        }

        data = {
            "sender": {
                "name": sender_name,
                "email": sender_email
            },
            "to": [
                {
                    "email": to_email
                }
            ],
            "subject": subject,
            "htmlContent": message_html
        }

        response = requests.post(
            url,
            headers=headers,
            json=data,
            timeout=15
        )

        if response.status_code in (200, 201, 202):
            print(
                f"[EMAIL OTP] Brevo sent email successfully "
                f"to {to_email}"
            )

            return (
                True,
                "Verification code sent to your email address."
            )

        try:
            error_data = response.json()
            error_message = error_data.get(
                "message",
                "Brevo rejected the email request."
            )
        except Exception:
            error_message = "Brevo rejected the email request."

        print(
            f"[EMAIL OTP] Brevo API failed. "
            f"Status: {response.status_code}. "
            f"Message: {error_message}"
        )

        return (
            False,
            "Email service is temporarily unavailable."
        )

    except requests.exceptions.Timeout:
        print("[EMAIL OTP] Brevo API request timed out.")

        return (
            False,
            "Email service is temporarily unavailable."
        )

    except requests.exceptions.RequestException as e:
        print(
            f"[EMAIL OTP] Brevo connection error: {str(e)}"
        )

        return (
            False,
            "Email service is temporarily unavailable."
        )

    except Exception as e:
        print(
            f"[EMAIL OTP] Email error: {str(e)}"
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
    provider = config.OTP_PROVIDER.lower().strip()

    if provider == 'gmail' or config.GMAIL_USER:
        return send_gmail_otp(
            target_email,
            otp
        )

    # Fallback log
    print("\n==========================================")
    print(
        f"[OTP LOG] Verification OTP for "
        f"{recipient}: {otp}"
    )
    print("==========================================\n")

    return True, f"Verification OTP: {otp}"