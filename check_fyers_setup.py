"""
check_fyers_setup.py
Checks if fyers-apiv3 SDK is installed and provides boilerplate
for Fyers API v3 authentication and connection.
"""

import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

print("=" * 65)
print("🔍 CHECKING FYERS API V3 SDK & DEPENDENCIES")
print("=" * 65)

try:
    import fyers_apiv3
    from fyers_apiv3 import fyersModel
    print("✅ fyers-apiv3 is INSTALLED!")
    print(f"   Version: {getattr(fyers_apiv3, '__version__', 'v3')}")
except ImportError:
    print("❌ fyers-apiv3 is NOT installed yet.")
    print("   Install command: pip install fyers-apiv3")

print("=" * 65)
