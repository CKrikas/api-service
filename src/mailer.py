import smtplib, os
from email.message import EmailMessage

SMTP_HOST = os.getenv("SMTP_HOST", "mailhog")
SMTP_PORT = int(os.getenv("SMTP_PORT", "1025"))
FROM_ADDR = os.getenv("SMTP_FROM", "noreply@stratologia.local")

def send_mail(to: str, subject: str, body: str):
    msg = EmailMessage()
    msg["From"] = FROM_ADDR
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
        s.send_message(msg)
