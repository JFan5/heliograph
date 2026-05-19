from __future__ import annotations

import os
import smtplib
import ssl
from abc import ABC, abstractmethod
from dataclasses import dataclass

import requests


class Sender(ABC):
    @abstractmethod
    def send(self, to: str | list[str], subject: str, html: str, text: str = "") -> None: ...


@dataclass
class SMTPConfig:
    host: str
    port: int
    username: str
    password: str
    use_tls: bool = True
    from_addr: str | None = None

    @classmethod
    def from_env(cls) -> "SMTPConfig":
        return cls(
            host=os.environ["SMTP_HOST"],
            port=int(os.environ.get("SMTP_PORT", "587")),
            username=os.environ["SMTP_USERNAME"],
            password=os.environ["SMTP_PASSWORD"],
            use_tls=os.environ.get("SMTP_USE_TLS", "true").lower() == "true",
            from_addr=os.environ.get("SMTP_FROM"),
        )


class SMTPSender(Sender):
    def __init__(self, config: SMTPConfig) -> None:
        self.config = config

    def send(self, to: str | list[str], subject: str, html: str, text: str = "") -> None:
        from email.message import EmailMessage

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self.config.from_addr or self.config.username
        msg["To"] = ", ".join(to) if isinstance(to, list) else to
        msg.set_content(text or "This email requires an HTML-capable client.")
        msg.add_alternative(html, subtype="html")

        if self.config.use_tls:
            context = ssl.create_default_context()
            with smtplib.SMTP(self.config.host, self.config.port) as server:
                server.starttls(context=context)
                server.login(self.config.username, self.config.password)
                server.send_message(msg)
        else:
            with smtplib.SMTP_SSL(self.config.host, self.config.port) as server:
                server.login(self.config.username, self.config.password)
                server.send_message(msg)


@dataclass
class MailgunConfig:
    api_key: str
    domain: str
    from_addr: str
    base_url: str = "https://api.mailgun.net/v3"

    @classmethod
    def from_env(cls) -> "MailgunConfig":
        return cls(
            api_key=os.environ["MAILGUN_API_KEY"],
            domain=os.environ["MAILGUN_DOMAIN"],
            from_addr=os.environ.get("MAILGUN_FROM") or os.environ["EMAIL_SENDER"],
            base_url=os.environ.get("MAILGUN_BASE_URL", "https://api.mailgun.net/v3"),
        )


class MailgunSender(Sender):
    def __init__(self, config: MailgunConfig) -> None:
        self.config = config

    def send(self, to: str | list[str], subject: str, html: str, text: str = "") -> None:
        url = f"{self.config.base_url}/{self.config.domain}/messages"
        recipients = to if isinstance(to, list) else [to]
        data = {
            "from": self.config.from_addr,
            "to": recipients,
            "subject": subject,
            "html": html,
        }
        if text:
            data["text"] = text
        resp = requests.post(url, auth=("api", self.config.api_key), data=data, timeout=30)
        if resp.status_code != 200:
            raise RuntimeError(f"Mailgun API error {resp.status_code}: {resp.text}")


def make_sender() -> Sender:
    """Build the sender selected by EMAIL_PROVIDER (mailgun|smtp). Default mailgun."""
    provider = os.environ.get("EMAIL_PROVIDER", "mailgun").lower()
    if provider == "mailgun":
        return MailgunSender(MailgunConfig.from_env())
    if provider == "smtp":
        return SMTPSender(SMTPConfig.from_env())
    raise ValueError(f"Unknown EMAIL_PROVIDER: {provider!r} (expected 'mailgun' or 'smtp')")


# Backwards-compat alias for the old single-class import.
EmailSender = SMTPSender
