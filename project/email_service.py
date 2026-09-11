import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from abc import ABC, abstractmethod
from config import config

class BaseEmailProvider(ABC):
    """Abstract Email Service Interface for pluggable Email providers."""
    
    @abstractmethod
    def send_email(self, to_email: str, subject: str, message: str) -> tuple[bool, str]:
        """Sends an Email message to specified email address."""
        pass


class SMTPProvider(BaseEmailProvider):
    """SMTP Email Gateway Implementation (e.g. Gmail)."""

    def send_email(self, to_email: str, subject: str, message: str) -> tuple[bool, str]:
        if not config.SMTP_USERNAME or not config.SMTP_PASSWORD:
            return False, "SMTP credentials missing."

        try:
            msg = MIMEMultipart()
            msg['From'] = config.SENDER_EMAIL
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(message, 'plain'))

            server = smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT)
            server.starttls()
            server.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
            server.send_message(msg)
            server.quit()
            
            return True, "Email sent via SMTP"
        except Exception as e:
            return False, f"SMTP exception: {str(e)}"


class ResendEmailProvider(BaseEmailProvider):
    """Resend HTTPS API Email Provider Implementation."""

    def send_email(self, to_email: str, subject: str, message: str) -> tuple[bool, str]:
        if not config.RESEND_API_KEY:
            return False, "Resend API key is not configured."

        try:
            import requests

            url = "https://api.resend.com/emails"
            headers = {
                "Authorization": f"Bearer {config.RESEND_API_KEY}",
                "Content-Type": "application/json"
            }
            data = {
                "from": config.SENDER_EMAIL or "TRY-FIT <onboarding@resend.dev>",
                "to": [to_email],
                "subject": subject,
                "text": message
            }

            response = requests.post(url, headers=headers, json=data, timeout=15)
            if response.status_code in (200, 201):
                return True, "Email sent via Resend API"

            try:
                err_data = response.json()
                err_msg = err_data.get("message", response.text)
            except Exception:
                err_msg = response.text

            return False, f"Resend API Error: {err_msg}"

        except requests.exceptions.Timeout:
            return False, "Resend API request timed out."
        except requests.exceptions.RequestException as e:
            return False, f"Resend Connection Error: {str(e)}"
        except Exception as e:
            return False, f"Resend Error: {str(e)}"


class ConsoleEmailProvider(BaseEmailProvider):
    """Console / Local Development Email Simulator Provider."""

    def send_email(self, to_email: str, subject: str, message: str) -> tuple[bool, str]:
        print(f"\n==========================================")
        print(f"[EMAIL CONSOLE PROVIDER] To: {to_email}")
        print(f"[SUBJECT]: {subject}")
        print(f"[MESSAGE]:\n{message}")
        print(f"==========================================\n")
        return True, "Email logged to console (Dev Mode)"


class EmailServiceFactory:
    """Factory to return configured Email provider instance."""

    @staticmethod
    def get_provider() -> BaseEmailProvider:
        provider_name = getattr(config, 'EMAIL_PROVIDER', 'console').lower().strip()
        if provider_name == 'resend':
            return ResendEmailProvider()
        elif provider_name == 'smtp':
            return SMTPProvider()
        else:
            return ConsoleEmailProvider()


def send_email(to_email: str, subject: str, message: str) -> tuple[bool, str]:
    """
    Global helper function to send Email via configured provider interface.
    Usage: send_email(to_email, subject, message)
    """
    provider = EmailServiceFactory.get_provider()
    success, msg = provider.send_email(to_email, subject, message)
    
    # If primary API fails, fallback to Console logging to prevent blocking dev workflow
    if not success:
        print(f"[Email Service Warning] {provider.__class__.__name__} failed: {msg}")
        ConsoleEmailProvider().send_email(to_email, subject, message)
        return True, f"OTP dispatched (Console Fallback: {msg})"
    return success, msg
