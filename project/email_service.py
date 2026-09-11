
import config
from abc import ABC, abstractmethod


class BaseEmailProvider(ABC):
    """Abstract Email Service Interface for pluggable Email providers."""

    @abstractmethod
    def send_email(
        self,
        to_email: str,
        subject: str,
        message: str
    ) -> tuple[bool, str]:
        """Send an email to the specified email address."""
        pass


class ResendEmailProvider(BaseEmailProvider):
    """Resend HTTPS API Email Provider."""

    def send_email(
        self,
        to_email: str,
        subject: str,
        message: str
    ) -> tuple[bool, str]:

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
                "from": config.SENDER_EMAIL,
                "to": [to_email],
                "subject": subject,
                "text": message
            }

            response = requests.post(
                url,
                headers=headers,
                json=data,
                timeout=15
            )

            if response.status_code in (200, 201):
                return True, "Email sent via Resend API"

            try:
                error_data = response.json()
                error_message = error_data.get(
                    "message",
                    response.text
                )
            except Exception:
                error_message = response.text

            return False, f"Resend API Error: {error_message}"

        except requests.exceptions.Timeout:
            return False, "Resend API request timed out."

        except requests.exceptions.RequestException as e:
            return False, f"Resend Connection Error: {str(e)}"

        except Exception as e:
            return False, f"Resend Error: {str(e)}"


class ConsoleEmailProvider(BaseEmailProvider):
    """Console Email Provider for local development."""

    def send_email(
        self,
        to_email: str,
        subject: str,
        message: str
    ) -> tuple[bool, str]:

        print("\n==========================================")
        print(f"[EMAIL CONSOLE PROVIDER] To: {to_email}")
        print(f"[SUBJECT]: {subject}")
        print(f"[MESSAGE]:\n{message}")
        print("==========================================\n")

        return True, "Email logged to console (Dev Mode)"


class EmailServiceFactory:
    """Factory that returns the configured email provider."""

    @staticmethod
    def get_provider() -> BaseEmailProvider:

        provider_name = getattr(
            config,
            "EMAIL_PROVIDER",
            "resend"
        ).lower().strip()

        if provider_name == "resend":
            return ResendEmailProvider()

        return ConsoleEmailProvider()


def send_email(
    to_email: str,
    subject: str,
    message: str
) -> tuple[bool, str]:
    """
    Send email using the configured email provider.
    """

    provider = EmailServiceFactory.get_provider()

    success, result_message = provider.send_email(
        to_email,
        subject,
        message
    )

    if not success:
        print(
            f"[Email Service Warning] "
            f"{provider.__class__.__name__} failed: "
            f"{result_message}"
        )

        # Development fallback.
        # This prevents the application from crashing if
        # the email provider is temporarily unavailable.
        ConsoleEmailProvider().send_email(
            to_email,
            subject,
            message
        )

        return (
            True,
            f"OTP dispatched "
            f"(Console Fallback: {result_message})"
        )

    return success, result_message

