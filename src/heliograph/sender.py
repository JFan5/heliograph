from __future__ import annotations

import os
import smtplib
import ssl
from dataclasses import dataclass
from email.message import EmailMessage


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


class EmailSender:
    def __init__(self, config: SMTPConfig) -> None:
        self.config = config

    def send(self, to: str | list[str], subject: str, html: str, text: str = "") -> None:
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
