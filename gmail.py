# gmail.py
# Create Gmail drafts and send emails with optional attachments

import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials


def _build_message(
    to: list[str],
    subject: str,
    body: str,
    attachment: dict | None = None,
) -> str:
    """Build a base64url-encoded RFC 2822 email message."""
    if attachment:
        msg = MIMEMultipart()
        msg.attach(MIMEText(body, "plain"))

        part = MIMEBase(*attachment["mime_type"].split("/"))
        part.set_payload(attachment["data"])
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f'attachment; filename="{attachment["name"]}"',
        )
        msg.attach(part)
    else:
        msg = MIMEText(body, "plain")

    msg["To"] = ", ".join(to)
    msg["Subject"] = subject

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    return raw


def create_draft(
    creds: Credentials,
    to: list[str],
    subject: str,
    body: str,
    attachment: dict | None = None,
) -> dict:
    """
    Save the email as a Gmail Draft (does not send).
    attachment = {"name": str, "mime_type": str, "data": bytes}
    """
    service = build("gmail", "v1", credentials=creds)
    raw = _build_message(to, subject, body, attachment)

    draft = (
        service.users()
        .drafts()
        .create(userId="me", body={"message": {"raw": raw}})
        .execute()
    )
    return draft


def send_email(
    creds: Credentials,
    to: list[str],
    subject: str,
    body: str,
    attachment: dict | None = None,
) -> dict:
    """
    Send the email immediately via Gmail API.
    attachment = {"name": str, "mime_type": str, "data": bytes}
    """
    service = build("gmail", "v1", credentials=creds)
    raw = _build_message(to, subject, body, attachment)

    result = (
        service.users()
        .messages()
        .send(userId="me", body={"raw": raw})
        .execute()
    )
    return result
