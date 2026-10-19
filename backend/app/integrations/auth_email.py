import asyncio
import smtplib
import ssl
from email.message import EmailMessage
from typing import Protocol

from pydantic import SecretStr

from app.core.config import Settings


class EmailDeliveryError(RuntimeError):
    """Raised when an authentication email cannot be delivered."""


class AuthEmailSender(Protocol):
    async def send_verification(self, *, recipient: str, token: str) -> None: ...

    async def send_password_reset(self, *, recipient: str, token: str) -> None: ...


class SMTPAuthEmailSender:
    """Provider-neutral SMTP adapter used by local development and configured environments."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._host = settings.auth_email_smtp_host
        if self._host is None and settings.app_env == "development":
            self._host = "127.0.0.1"

    @property
    def is_configured(self) -> bool:
        if self._host is None:
            return False
        if (
            self._settings.auth_email_smtp_username is not None
            and self._settings.auth_email_smtp_password is None
        ):
            return False
        return not (
            self._settings.app_env in {"staging", "production"}
            and not (self._settings.auth_email_smtp_ssl or self._settings.auth_email_smtp_starttls)
        )

    async def send_verification(self, *, recipient: str, token: str) -> None:
        message = EmailMessage()
        message["Subject"] = "Verify your Community account"
        message.set_content(
            "To verify your email, send this JSON to POST /api/v1/auth/verify-email:\n\n"
            f'{{"token": "{token}"}}\n'
        )
        await self._send(recipient, message)

    async def send_password_reset(self, *, recipient: str, token: str) -> None:
        message = EmailMessage()
        message["Subject"] = "Reset your Community password"
        message.set_content(
            "To reset your password, include this token in POST "
            "/api/v1/auth/password/reset:\n\n"
            f'{{"token": "{token}", "new_password": "<your-new-password>"}}\n'
        )
        await self._send(recipient, message)

    async def _send(self, recipient: str, message: EmailMessage) -> None:
        if not self.is_configured:
            raise EmailDeliveryError("Authentication email delivery is not configured")

        message["From"] = self._settings.auth_email_from_address
        message["To"] = recipient
        try:
            await asyncio.to_thread(self._send_blocking, message)
        except (OSError, smtplib.SMTPException, ssl.SSLError) as error:
            raise EmailDeliveryError("Authentication email delivery failed") from error

    def _send_blocking(self, message: EmailMessage) -> None:
        password = self._settings.auth_email_smtp_password
        if self._settings.auth_email_smtp_ssl:
            with smtplib.SMTP_SSL(
                self._host,
                self._settings.auth_email_smtp_port,
                timeout=self._settings.auth_email_timeout_seconds,
                context=ssl.create_default_context(),
            ) as client:
                self._login_if_configured(client, password)
                client.send_message(message)
            return

        with smtplib.SMTP(
            self._host,
            self._settings.auth_email_smtp_port,
            timeout=self._settings.auth_email_timeout_seconds,
        ) as client:
            if self._settings.auth_email_smtp_starttls:
                client.starttls(context=ssl.create_default_context())
            self._login_if_configured(client, password)
            client.send_message(message)

    def _login_if_configured(
        self,
        client: smtplib.SMTP | smtplib.SMTP_SSL,
        password: SecretStr | None,
    ) -> None:
        username = self._settings.auth_email_smtp_username
        if username is None:
            return
        if password is None:
            raise EmailDeliveryError("SMTP password is missing")
        secret = password.get_secret_value()
        client.login(username, secret)
