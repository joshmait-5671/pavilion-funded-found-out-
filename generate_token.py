"""One-time script: generates auth/token.json via OAuth browser flow."""
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/gmail.send']
auth_dir = Path(__file__).parent / 'auth'
secrets_path = auth_dir / 'client_secrets.json'
token_path = auth_dir / 'token.json'

flow = InstalledAppFlow.from_client_secrets_file(str(secrets_path), SCOPES)
creds = flow.run_local_server(port=0)

with open(str(token_path), 'w') as f:
    f.write(creds.to_json())

print(f"✅ Token saved to {token_path}")
