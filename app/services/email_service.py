from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import aiosmtplib
from jinja2 import Environment, FileSystemLoader

from app.core.config import settings


class EmailService:
    def __init__(self):
        template_dir = Path(__file__).parent.parent / "templates" / "emails"
        self.jinja = Environment(loader=FileSystemLoader(str(template_dir)))

    async def send_email(
            self,
            to: str,
            subject: str,
            template_name: str,
            context: dict
    ) -> bool:
        """Send and email using jinja template"""
        try:
            template = self.jinja.get_template(template_name)
            html_content = template.render(**context)

            message = MIMEMultipart("alternative")
            message["From"] = settings.EMAIL_FROM
            message["To"] = to
            message["Subject"] = subject
            message.attach(MIMEText(html_content, "html"))

            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                start_tls=True,
            )
            return True
        except Exception as e:
            print (f"Email error: {e}")
            return False

def get_email_service() -> EmailService:
    return EmailService()
