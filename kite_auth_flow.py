"""
Kite Connect Authentication Flow
This script handles the manual login process to generate a session access token.
"""

import os
from pathlib import Path
from kiteconnect import KiteConnect
from configuration.swing_trade_settings import load_settings

def main():
    print("==================================================")
    print("   ZERODHA KITE AUTHENTICATION FLOW")
    print("==================================================")
    
    settings = load_settings()
    
    if not settings.zerodha_api_key:
        print("Error: ZERODHA_API_KEY is missing in .env file.")
        return

    kite = KiteConnect(api_key=settings.zerodha_api_key)
    
    # 1. Generate Login URL
    login_url = kite.login_url()
    print("\nStep 1: Log in to Zerodha")
    print(f"Please visit this URL in your browser:\n\n{login_url}\n")
    
    # 2. Get Request Token
    print("Step 2: Get the Request Token")
    print("After logging in, you will be redirected to your redirect URL.")
    print("Copy the 'request_token' parameter from the browser URL.")
    request_token = input("\nEnter the request token: ").strip()
    
    if not request_token:
        print("Error: Request token cannot be empty.")
        return
    
    try:
        # 3. Generate Access Token
        print("\nExchanging request token for access token...")
        data = kite.generate_session(request_token, secret=os.getenv("ZERODHA_API_SECRET", ""))
        access_token = data["access_token"]
        
        # 4. Save to File
        token_file = settings.access_token_file
        with open(token_file, "w", encoding="utf-8") as f:
            f.write(f"ACCESS_TOKEN={access_token}")
            
        print("\n==================================================")
        print(f"SUCCESS: Access token saved to {token_file}")
        print("You can now run your scanners.")
        print("==================================================")
        
    except Exception as e:
        print(f"\nError generating session: {e}")
        print("Ensure your ZERODHA_API_SECRET is correct in the .env file.")

if __name__ == "__main__":
    main()
