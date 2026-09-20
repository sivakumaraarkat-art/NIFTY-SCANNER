"""
STOCK SWING V1
Zerodha Known Stocks Quote Diagnostic

Purpose:
- Test Zerodha quote() using known highly liquid NSE stocks.
- Check last_price, volume, average_price and OHLC.
- Help determine whether zero volume is caused by market/session timing.

READ-ONLY:
- No orders.
- No historical-data requests.
- No scanner changes.
- Does not print API keys or access tokens.
"""

from __future__ import annotations

from configuration.swing_trade_settings import load_settings
from zerodha_market_data.zerodha_connection import (
    create_zerodha_client,
    verify_connection,
)

TEST_SYMBOLS = [
    "NSE:RELIANCE",
    "NSE:HDFCBANK",
    "NSE:INFY",
]


def main() -> None:

    print("=" * 70)
    print("STOCK SWING V1 - KNOWN STOCK QUOTE DIAGNOSTIC")
    print("=" * 70)

    # ---------------------------------------------------------------
    # 1. Load existing configuration
    # ---------------------------------------------------------------

    settings = load_settings()

    print("\n[1] Configuration loaded.")

    # ---------------------------------------------------------------
    # 2. Existing Zerodha connection
    # ---------------------------------------------------------------

    kite = create_zerodha_client(settings)

    verify_connection(kite)

    print("[2] Zerodha connection verified.")

    # ---------------------------------------------------------------
    # 3. Request quotes for ONLY three known stocks
    # ---------------------------------------------------------------

    print("\n[3] Testing instruments:")

    for instrument in TEST_SYMBOLS:
        print(f"    {instrument}")

    print("\nRequesting ONE read-only quote() call...")

    try:
        quote_data = kite.quote(TEST_SYMBOLS)

    except Exception as exc:

        print("\nERROR: Zerodha quote request failed.")

        print(f"Error type   : {type(exc).__name__}")

        print(f"Error message: {exc}")

        return

    # ---------------------------------------------------------------
    # 4. Validate response
    # ---------------------------------------------------------------

    print("\n[4] Quote response received.")

    if not isinstance(quote_data, dict):

        print("ERROR: Unexpected response type: " f"{type(quote_data).__name__}")

        return

    print(f"Instruments returned: {len(quote_data)}")

    # ---------------------------------------------------------------
    # 5. Display important fields
    # ---------------------------------------------------------------

    for instrument in TEST_SYMBOLS:

        print("\n" + "-" * 70)
        print(instrument)
        print("-" * 70)

        quote = quote_data.get(instrument)

        if not quote:

            print("NO QUOTE DATA RETURNED")

            continue

        print(f"last_price      : " f"{quote.get('last_price')}")

        print(f"average_price   : " f"{quote.get('average_price')}")

        print(f"volume          : " f"{quote.get('volume')}")

        print(f"net_change      : " f"{quote.get('net_change')}")

        print(f"oi              : " f"{quote.get('oi')}")

        print(f"oi_day_high     : " f"{quote.get('oi_day_high')}")

        print(f"oi_day_low      : " f"{quote.get('oi_day_low')}")

        # -----------------------------------------------------------
        # OHLC
        # -----------------------------------------------------------

        ohlc = quote.get("ohlc")

        print("\nOHLC:")

        if isinstance(ohlc, dict):

            print(f"    open  : {ohlc.get('open')}")

            print(f"    high  : {ohlc.get('high')}")

            print(f"    low   : {ohlc.get('low')}")

            print(f"    close : {ohlc.get('close')}")

        else:

            print(f"    {ohlc}")

        # -----------------------------------------------------------
        # Derived traded value
        # -----------------------------------------------------------

        try:

            last_price = float(quote.get("last_price") or 0)

            average_price = float(quote.get("average_price") or 0)

            volume = float(quote.get("volume") or 0)

        except (TypeError, ValueError):

            last_price = 0
            average_price = 0
            volume = 0

        reference_price = average_price if average_price > 0 else last_price

        estimated_traded_value = reference_price * volume

        print("\nDerived liquidity values:")

        print(f"    reference_price      : " f"{reference_price}")

        print(f"    estimated_traded_value: " f"₹{estimated_traded_value:,.2f}")

        # -----------------------------------------------------------
        # Interpretation
        # -----------------------------------------------------------

        if volume > 0:

            print("\n    STATUS: LIVE/SESSION VOLUME AVAILABLE")

        else:

            print("\n    STATUS: VOLUME IS ZERO")

    # ---------------------------------------------------------------
    # 6. Show available top-level fields
    # ---------------------------------------------------------------

    print("\n" + "=" * 70)
    print("AVAILABLE TOP-LEVEL QUOTE FIELDS")
    print("=" * 70)

    for instrument in TEST_SYMBOLS:

        quote = quote_data.get(instrument)

        if not quote:
            continue

        print(f"\n{instrument}:")

        for field_name in sorted(quote.keys()):

            print(f"    - {field_name}")

    # ---------------------------------------------------------------
    # 7. Safety confirmation
    # ---------------------------------------------------------------

    print("\n" + "=" * 70)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 70)

    print("\nNo scanner files were modified.")
    print("No historical-data requests were made.")
    print("No orders were placed.")
    print("\nSend me the complete output.")


if __name__ == "__main__":
    main()
