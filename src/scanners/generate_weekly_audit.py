import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import os


def upload_to_google_drive(output_file: str):
    """Upload the generated workbook to Google Drive using OAuth or a service account."""
    from dotenv import load_dotenv
    load_dotenv()

    auth_mode = os.getenv("GDRIVE_AUTH_MODE", "oauth").strip().lower()
    folder_id = os.getenv("GDRIVE_FOLDER_ID")
    if not folder_id:
        print("Skipping Google Drive upload: GDRIVE_FOLDER_ID is not set.")
        return False

    try:
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
    except ImportError:
        print("Failed to upload to Google Drive: Missing required Python packages.")
        print("Run: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
        return False

    try:
        if auth_mode in {"service_account", "service-account"}:
            creds_file = os.getenv("GDRIVE_CREDENTIALS_FILE")
            if not creds_file:
                print("Service-account mode requires GDRIVE_CREDENTIALS_FILE.")
                return False
            if not os.path.exists(creds_file):
                print(f"Missing Google Drive service-account file: {creds_file}")
                return False

            from google.oauth2.service_account import Credentials
            creds = Credentials.from_service_account_file(
                creds_file,
                scopes=["https://www.googleapis.com/auth/drive.file"],
            )
            service = build("drive", "v3", credentials=creds)
            print("Using Google Drive service-account auth.")

        elif auth_mode in {"oauth", "user", "desktop"}:
            client_secret_file = os.getenv("GDRIVE_CLIENT_SECRET_FILE") or os.getenv("GDRIVE_CREDENTIALS_FILE")
            token_file = os.getenv("GDRIVE_TOKEN_FILE", "google_drive_token.json")
            if not client_secret_file:
                print("OAuth mode requires GDRIVE_CLIENT_SECRET_FILE (downloaded OAuth client JSON).")
                return False
            if not os.path.exists(client_secret_file):
                print(f"Missing Google Drive OAuth client secret file: {client_secret_file}")
                return False

            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials as GoogleCredentials
            from google_auth_oauthlib.flow import InstalledAppFlow

            scopes = ["https://www.googleapis.com/auth/drive.file"]
            creds = None
            if os.path.exists(token_file):
                creds = GoogleCredentials.from_authorized_user_file(token_file, scopes)

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(client_secret_file, scopes)
                    creds = flow.run_local_server(port=0)
                    with open(token_file, "w", encoding="utf-8") as token_handle:
                        token_handle.write(creds.to_json())

            service = build("drive", "v3", credentials=creds)
            print("Using Google Drive OAuth user auth.")

        else:
            print(
                f"Unsupported GDRIVE_AUTH_MODE '{auth_mode}'. Use 'oauth' or 'service_account'."
            )
            return False

    except Exception as auth_error:
        print(f"Google Drive auth setup failed: {auth_error}")
        return False

    try:
        file_metadata = {
            "name": output_file,
            "parents": [folder_id]
        }

        media = MediaFileUpload(
            output_file,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            resumable=True,
        )

        uploaded_file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id, webViewLink",
            supportsAllDrives=True,
        ).execute()

        print("Successfully uploaded to Google Drive!")
        print(f"Google Drive Link: {uploaded_file.get('webViewLink')}")
        return True

    except Exception as gd_e:
        print(f"Google Drive upload failed: {gd_e}")
        print("If using a personal Google Drive folder, switch to OAuth mode or use a Shared Drive.")
        return False


def generate_weekly_audit_excel():
    log_dir = Path("logs")
    if not log_dir.exists():
        print("No logs directory found.")
        return

    all_signals = []
    
    # Sweep all JSON logs
    for log_file in log_dir.glob("*.json"):
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Determine scanner type
            filename = log_file.name
            if "intraday" in filename:
                strategy = "INTRADAY"
            elif "btst" in filename:
                strategy = "BTST"
            elif "news" in filename:
                strategy = "NEWS"
            else:
                strategy = "OTHER"
                
            date_generated = datetime.fromtimestamp(log_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
            
            # Look for candidates
            candidates = []
            if "candidates" in data:
                candidates = data["candidates"] # Intraday format
            elif "results" in data and "stocks" in data["results"]:
                candidates = data["results"]["stocks"] + data["results"].get("index", []) # BTST format
                
            for c in candidates:
                if isinstance(c, dict) and "symbol" in c:
                    all_signals.append({
                        "Date Generated": date_generated,
                        "Strategy": strategy,
                        "Symbol": c.get("symbol", ""),
                        "Type": c.get("option_type", "EQ"),
                        "Strike": c.get("strike", ""),
                        "Signal Entry (₹)": c.get("ltp", ""),
                        "Powerful SL (₹)": c.get("powerful_sl", c.get("sl", "")),
                        "Target 1 (₹)": c.get("t1", ""),
                        "Target 2 (₹)": c.get("t2", ""),
                        "Score": c.get("score", ""),
                        "Your Actual Exit (₹)": "",   # User fills this manually
                        "Actual P&L": "",             # User fills this manually
                        "Audit Notes": ""             # User fills this manually
                    })
        except Exception as e:
            continue

    if not all_signals:
        print("No signals found in logs.")
        return

    df = pd.DataFrame(all_signals)
    df = df.sort_values(by="Date Generated", ascending=False)
    
    output_file = f"Weekly_Trade_Audit_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
    
    # Save using default pandas engine (usually openpyxl)
    df.to_excel(output_file, index=False, sheet_name='Signal Audit')

    print(f"\nCreated Audit Tracker: {output_file}")

    # Send directly to Telegram since this will run on a VM
    try:
        from dotenv import load_dotenv
        import requests

        load_dotenv()
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")

        if bot_token and chat_id:
            print("Sending Excel file directly to your Telegram...")
            url = f"https://api.telegram.org/bot{bot_token}/sendDocument"

            with open(output_file, "rb") as f:
                files = {"document": (output_file, f)}
                data = {
                    "chat_id": chat_id,
                    "caption": "📊 <b>Weekly Trade Audit Ready!</b>\n\nSince this runs on a Cloud VM, I've sent the Excel file directly to you here.\n\nOpen it on your phone or PC to log your manual results.",
                    "parse_mode": "HTML"
                }

                response = requests.post(url, data=data, files=files, timeout=30)

                if response.status_code == 200:
                    print("Successfully delivered to Telegram!")
                else:
                    print(f"Failed to send to Telegram: {response.text}")

        # ----------- GOOGLE DRIVE UPLOAD LOGIC -----------
        upload_to_google_drive(output_file)

    except Exception as e:
        print(f"Uploads failed: {e}")

if __name__ == "__main__":
    generate_weekly_audit_excel()
