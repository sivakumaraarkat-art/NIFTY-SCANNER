"""
Kite Connect Authentication Flow
This script handles the login process to generate a session access token.
"""

import os
import sys
import json
import urllib.parse
from pathlib import Path
from kiteconnect import KiteConnect
from configuration.swing_trade_settings import load_settings

def find_credentials():
    candidates = [
        Path(".credentials.json"),
        Path("../.credentials.json"),
        Path("D:/NiftyScanner/PORTFOLIO_PEAK_EXIT_GUARD/.credentials.json"),
        Path("D:/NiftyScanner/.credentials.json"),
    ]
    for c in candidates:
        if c.exists():
            try:
                with open(c, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("zerodha", {})
            except Exception:
                pass
    return {}

def main():
    print("==================================================")
    print("   ZERODHA KITE AUTHENTICATION FLOW")
    print("==================================================")

    settings = load_settings()
    cred = find_credentials()

    api_key = os.getenv("ZERODHA_API_KEY") or settings.zerodha_api_key or cred.get("api_key")
    api_secret = os.getenv("ZERODHA_API_SECRET") or cred.get("api_secret")

    if not api_key:
        print("❌ Error: ZERODHA_API_KEY is missing.")
        return

    if not api_secret:
        print("❌ Error: ZERODHA_API_SECRET is missing.")
        return

    kite = KiteConnect(api_key=api_key)

    # 1. Generate Login URL
    login_url = kite.login_url()
    print("\nStep 1: Open this URL in your browser to log in:")
    print("-" * 55)
    print(login_url)
    print("-" * 55)

    # 2. Get Request Token (or full redirected URL)
    print("\nStep 2: After logging in, you will be redirected.")
    print("Copy the 'request_token' OR paste the entire redirected URL here:")
    raw_input = input("\nEnter request_token or redirect URL: ").strip()

    if not raw_input:
        print("❌ Error: Input cannot be empty.")
        return

    # Extract request_token if user pasted the entire URL
    request_token = raw_input
    if "request_token=" in raw_input:
        parsed = urllib.parse.urlparse(raw_input)
        params = urllib.parse.parse_qs(parsed.query)
        if "request_token" in params:
            request_token = params["request_token"][0]

    request_token = request_token.strip()
    print(f"\nExchanging request token ({request_token[:8]}...) for access token...")

    try:
        # 3. Generate Access Token
        data = kite.generate_session(request_token, api_secret=api_secret)
        access_token = data.get("access_token")

        if not access_token:
            print("❌ Error: Access token was missing from Kite response.")
            return

        kite.set_access_token(access_token)
        profile = kite.profile()
        user_name = profile.get("user_name", "Zerodha Trader")
        user_id = profile.get("user_id", "")

        # 4. Save to files across project locations
        save_paths = [
            Path(".kite_access_token"),
            Path("D:/NiftyScanner/.kite_access_token"),
            Path(settings.access_token_file) if hasattr(settings, "access_token_file") else None
        ]

        for p in save_paths:
            if p:
                try:
                    p.parent.mkdir(parents=True, exist_ok=True)
                    p.write_text(access_token, encoding="utf-8")
                    print(f"✓ Saved access token to: {p}")
                except Exception as ex:
                    print(f"⚠️ Could not write to {p}: {ex}")

        # Also save active api_key
        key_paths = [
            Path(".kite_api_key"),
            Path("D:/NiftyScanner/.kite_api_key"),
        ]
        for p in key_paths:
            try:
                p.write_text(api_key, encoding="utf-8")
            except Exception:
                pass

        print("\n==================================================")
        print(f"🎉 SUCCESS! Logged in as: {user_name} ({user_id})")
        print("Zerodha Kite API is now authenticated and ACTIVE.")
        print("==================================================")

    except Exception as e:
        print(f"\n❌ Error generating session: {e}")
        print("Please check if the request token was already used or expired.")

if __name__ == "__main__":
    main()
