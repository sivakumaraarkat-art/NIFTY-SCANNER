"""
generate_fresh_kite_token.py
Automated Zerodha Kite Login & Access Token Generator via TOTP
"""

import sys
import os
import io
import json
import urllib.parse
from pathlib import Path

# UTF-8 fix for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

try:
    import pyotp
except ImportError:
    print("❌ pyotp not installed. Install with: pip install pyotp")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("❌ requests not installed. Install with: pip install requests")
    sys.exit(1)

try:
    from kiteconnect import KiteConnect
except ImportError:
    print("❌ kiteconnect not installed. Install with: pip install kiteconnect")
    sys.exit(1)

def find_credentials():
    candidates = [
        Path(".credentials.json"),
        Path("../.credentials.json"),
        Path("D:/NiftyScanner/PORTFOLIO_PEAK_EXIT_GUARD/.credentials.json"),
        Path("D:/NiftyScanner/VM/nifty_v14_7/.credentials.json"),
        Path("D:/NiftyScanner/.credentials.json"),
    ]
    for c in candidates:
        if c.exists():
            try:
                with open(c, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "zerodha" in data:
                        return data["zerodha"]
            except Exception:
                pass
    return None

def main():
    print("=" * 65)
    print("🔑 AUTOMATED ZERODHA KITE ACCESS TOKEN GENERATOR (TOTP)")
    print("=" * 65)

    cred = find_credentials()
    if not cred:
        print("❌ Could not locate .credentials.json file.")
        return

    user_id = cred.get("user_id")
    password = cred.get("password")
    totp_secret = cred.get("totp_secret")
    api_key = cred.get("api_key")
    api_secret = cred.get("api_secret")

    if not all([user_id, password, totp_secret, api_key, api_secret]):
        print("❌ Missing one or more required Zerodha credentials in .credentials.json.")
        return

    totp_secret = str(totp_secret).replace(" ", "").replace("-", "").strip().upper()

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    })

    print(f"[*] Step 1: Submitting credentials for user {user_id}...")
    try:
        login_resp = session.post(
            "https://kite.zerodha.com/api/login",
            data={"user_id": user_id, "password": password},
            timeout=12
        )
        login_data = login_resp.json()
    except Exception as e:
        print(f"❌ Login network error: {e}")
        return

    if login_data.get("status") != "success":
        print(f"❌ Login rejected by Zerodha: {login_data.get('message')}")
        return

    request_id = login_data.get("data", {}).get("request_id")
    if not request_id:
        print("❌ Failed to obtain request_id from Zerodha.")
        return
    print(f"   ✓ Step 1 complete. request_id obtained.")

    # Generate TOTP
    try:
        totp = pyotp.TOTP(totp_secret)
        twofa_value = totp.now()
    except Exception as e:
        print(f"❌ TOTP generation error: {e}")
        return

    print(f"[*] Step 2: Submitting 2FA TOTP ({twofa_value})...")
    try:
        twofa_resp = session.post(
            "https://kite.zerodha.com/api/twofa",
            data={
                "user_id": user_id,
                "request_id": request_id,
                "twofa_value": twofa_value,
                "twofa_type": "totp",
                "skip_session": "",
            },
            timeout=12
        )
        twofa_data = twofa_resp.json()
    except Exception as e:
        print(f"❌ 2FA network error: {e}")
        return

    if twofa_data.get("status") != "success":
        print(f"❌ 2FA verification rejected: {twofa_data.get('message')}")
        return
    print("   ✓ Step 2 complete. 2FA verified.")

    # Follow OAuth redirect chain to get request_token
    print(f"[*] Step 3: Fetching OAuth redirect for API Key {api_key}...")
    connect_url = f"https://kite.zerodha.com/connect/login?api_key={api_key}&v=3"
    current_url = connect_url
    request_token = None

    try:
        for _ in range(5):
            r = session.get(current_url, allow_redirects=False, timeout=12)
            loc = r.headers.get("Location")
            if not loc:
                break
            parsed = urllib.parse.urlparse(loc)
            params = urllib.parse.parse_qs(parsed.query)
            if "request_token" in params:
                request_token = params["request_token"][0]
                break
            if loc.startswith("/"):
                current_url = f"https://kite.zerodha.com{loc}"
            else:
                current_url = loc
    except Exception as e:
        print(f"❌ OAuth redirect error: {e}")
        return

    if not request_token:
        print("❌ Could not capture request_token from redirect headers.")
        return
    print(f"   ✓ Step 3 complete. request_token captured: {request_token[:8]}...")

    # Exchange request_token for access_token
    print(f"[*] Step 4: Exchanging request_token for access_token...")
    try:
        kite = KiteConnect(api_key=api_key)
        sess = kite.generate_session(request_token, api_secret=api_secret)
        access_token = sess.get("access_token")
    except Exception as e:
        print(f"❌ Kite generate_session error: {e}")
        return

    if not access_token:
        print("❌ Access token was empty in session response.")
        return

    # Verify connection
    kite.set_access_token(access_token)
    profile = kite.profile()
    user_name = profile.get("user_name", "Zerodha Trader")
    print(f"\n🎉 AUTHENTICATION SUCCESSFUL! Logged in as: {user_name} ({user_id})")

    # Save to all token locations
    save_targets = [
        Path(".kite_access_token"),
        Path("D:/NiftyScanner/.kite_access_token"),
        Path("D:/NiftyScanner/PORTFOLIO_PEAK_EXIT_GUARD/.kite_access_token")
    ]

    for target in save_targets:
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(access_token, encoding="utf-8")
            print(f"   ✓ Saved token to: {target}")
        except Exception as ex:
            print(f"   ⚠️ Could not save to {target}: {ex}")

    key_targets = [
        Path(".kite_api_key"),
        Path("D:/NiftyScanner/.kite_api_key"),
    ]
    for target in key_targets:
        try:
            target.write_text(api_key, encoding="utf-8")
        except Exception:
            pass

    print("=" * 65)
    print("✅ Zerodha Kite Token is now 100% active and synchronized.")
    print("   Now running live quote verification on NSE:RVNL...")
    try:
        q = kite.quote(["NSE:RVNL"])
        rvnl_ltp = q["NSE:RVNL"]["last_price"]
        print(f"   📡 LIVE ZERODHA QUOTE TEST: NSE:RVNL LTP = ₹{rvnl_ltp}")
    except Exception as e:
        print(f"   ⚠️ Quote test warning: {e}")
    print("=" * 65)

if __name__ == "__main__":
    main()
