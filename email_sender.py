import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv


load_dotenv()


SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "Sales AI")
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"


def parse_subject_and_body(email_text: str) -> tuple[str, str]:
    """
    Try to split out a 'Subject:' line if present.
    If none is found, use a generic subject.
    """
    lines = [l for l in email_text.splitlines() if l.strip() != ""]
    subject = "Quick idea for you"
    body = email_text

    for i, line in enumerate(lines):
        lower = line.lower()
        if lower.startswith("subject:"):
            subject = line.split(":", 1)[1].strip() or subject
            body = "\n".join(lines[i + 1 :])
            break

    return subject, body


def send_email(to_address: str, email_text: str) -> None:
    """
    Sends an email via SMTP.
    If DRY_RUN=true (default), just prints to the console instead
    of actually sending.
    """
    subject, body = parse_subject_and_body(email_text)

    if DRY_RUN:
        print("=" * 80)
        print(f"[DRY RUN] Would send email to: {to_address}")
        print(f"Subject: {subject}")
        print("-" * 80)
        print(body)
        print("=" * 80)
        return

    if not SMTP_USERNAME or not SMTP_PASSWORD:
        raise RuntimeError("SMTP_USERNAME and SMTP_PASSWORD must be set when DRY_RUN is false.")

    msg = MIMEMultipart()
    msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_USERNAME}>"
    msg["To"] = to_address
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)

