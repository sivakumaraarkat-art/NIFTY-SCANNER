import os
from pathlib import Path

from dotenv import load_dotenv


SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def main():
    load_dotenv()

    client_secret_file = os.getenv("GDRIVE_CLIENT_SECRET_FILE") or "client_secret.json"
    token_file = os.getenv("GDRIVE_TOKEN_FILE") or "google_drive_token.json"

    client_secret_path = Path(client_secret_file)
    if not client_secret_path.exists():
        print(f"Missing OAuth client file: {client_secret_path}")
        print("Create an OAuth 2.0 Client ID in Google Cloud Console and download the JSON file into this folder.")
        return

    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    creds = None
    if Path(token_file).exists():
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Token refresh failed ({e}). Re-authenticating via browser...")
                flow = InstalledAppFlow.from_client_secrets_file(str(client_secret_path), SCOPES)
                creds = flow.run_local_server(port=0)
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(client_secret_path), SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_file, "w", encoding="utf-8") as token_handle:
            token_handle.write(creds.to_json())

    print(f"Google Drive OAuth token saved to: {token_file}")

    # Auto-sync to Cloud VM
    ssh_key = Path("D:/NiftyScanner/oracle/nifty-v15.key")
    if ssh_key.exists():
        print("[*] Syncing fresh token to Cloud VM...")
        cmd = f'scp -i "{ssh_key}" "{token_file}" ubuntu@140.245.195.112:/home/ubuntu/NiftyScanner/STOCK_SWING_V1_updated/{token_file}'
        os.system(cmd)
        print("[+] Cloud VM token synchronized successfully!")


if __name__ == "__main__":
    main()
