"""Send the weekly Funded & Found Out report via Gmail API."""
import base64
import logging
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from pathlib import Path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/gmail.send']


def get_gmail_service(auth_dir: Path):
    """Authenticate and return Gmail API service. Runs OAuth flow on first use."""
    creds = None
    token_path = auth_dir / 'token.json'
    secrets_path = auth_dir / 'client_secrets.json'

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(secrets_path), SCOPES)
            creds = flow.run_local_server(port=0)
        with open(str(token_path), 'w') as f:
            f.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)


def send_report(
    pdf_path: Path,
    auth_dir: Path,
    to_email: str,
    from_email: str,
    company_names: list[str],
) -> bool:
    """Send the weekly carousel PDF to the recipient."""
    try:
        service = get_gmail_service(auth_dir)

        date_str = datetime.now().strftime("%B %d, %Y")
        names_str = ', '.join(company_names)

        subject = f"Funded & Found Out — {date_str}"

        body = f"""Hey Josh,

Your weekly Funded & Found Out report is attached and ready for Thursday.

This week's companies: {names_str}

The PDF is formatted as a LinkedIn carousel. Upload it directly to a LinkedIn post as a document — LinkedIn will auto-render it as a swipeable carousel.

—
Funded & Found Out Bot 🤖
"""

        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        with open(pdf_path, 'rb') as f:
            attachment = MIMEBase('application', 'pdf')
            attachment.set_payload(f.read())
            encoders.encode_base64(attachment)
            attachment.add_header(
                'Content-Disposition',
                f'attachment; filename="{pdf_path.name}"',
            )
            msg.attach(attachment)

        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        service.users().messages().send(userId='me', body={'raw': raw}).execute()

        logger.info(f"Report sent: {pdf_path.name} → {to_email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send report: {e}")
        return False
