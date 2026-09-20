"""
STOCK SWING V1
Zerodha Quote Diagnostic

Purpose:
- Verify the actual Zerodha quote() response.
- Diagnose why quote liquidity currently returns 0 stocks.
- Does NOT modify scanner logic.
- Does NOT place any orders.
- Does NOT print API keys or access tokens.

Run manually:
    python test_zerodha_quote_response.py
"""

from __future__ import annotations

from configuration.swing_trade_settings import load_settings
from zerodha_market_data.zerodha_connection import (
    create_zerodha_client,
    verify_connection,
)
from stock_universe.nse_stock_universe import load_nse_equity_universe


def main() -> None:
    print("=" * 70)
    print("STOCK SWING V1 - ZERODHA QUOTE DIAGNOSTIC")
    print("=" * 70)

    # ---------------------------------------------------------------
    # 1. Load existing configuration
    # ---------------------------------------------------------------
    settings = load_settings()
    print("\n[1] Configuration loaded.")

    # ---------------------------------------------------------------
    # 2. Connect using the EXISTING Zerodha configuration
    # ---------------------------------------------------------------
    kite = create_zerodha_client(settings)
    verify_connection(kite)

    print("[2] Zerodha connection verified.")

    # ---------------------------------------------------------------
    # 3. Load the existing stock universe
    # ---------------------------------------------------------------
    universe = load_nse_equity_universe(
        kite,
        settings,
    )

    print(f"[3] Stock candidates available: " f"{len(universe)}")

    if not universe:
        print("ERROR: No stock candidates found.")
        return

    # ---------------------------------------------------------------
    # 4. Select only the first 5 candidates
    # ---------------------------------------------------------------
    test_candidates = universe[:5]

    symbols = [
        str(item["tradingsymbol"]).strip().upper()
        for item in test_candidates
        if item.get("tradingsymbol")
    ]

    if not symbols:
        print("ERROR: No valid symbols available.")
        return

    print("\n[4] Testing symbols:")
    for symbol in symbols:
        print(f"    NSE:{symbol}")

    instruments = [f"NSE:{symbol}" for symbol in symbols]

    # ---------------------------------------------------------------
    # 5. Make ONE quote API request
    # ---------------------------------------------------------------
    print("\n[5] Requesting Zerodha quote data...")
    print("    This is ONE read-only API request.")

    try:
        quote_data = kite.quote(instruments)

    except Exception as exc:
        print("\nERROR: Zerodha quote request failed.")
        print(f"Error type   : {type(exc).__name__}")
        print(f"Error message: {exc}")
        return

    # ---------------------------------------------------------------
    # 6. Basic response check
    # ---------------------------------------------------------------
    print("\n[6] Quote response received.")

    if not isinstance(quote_data, dict):
        print(f"ERROR: Unexpected response type: " f"{type(quote_data).__name__}")
        return

    print(f"Response instruments returned: " f"{len(quote_data)}")

    # ---------------------------------------------------------------
    # 7. Inspect actual fields
    # ---------------------------------------------------------------
    print("\n[7] ACTUAL QUOTE FIELDS")
    print("-" * 70)

    for symbol in symbols:

        key = f"NSE:{symbol}"
        quote = quote_data.get(key)

        print(f"\n{key}")

        if not quote:
            print("  NO QUOTE DATA RETURNED")
            continue

        print(f"  Response type: " f"{type(quote).__name__}")

        print("  Available fields:")

        for field_name in sorted(quote.keys()):
            print(f"    - {field_name}")

        # -----------------------------------------------------------
        # 8. Show only the fields relevant to liquidity
        # -----------------------------------------------------------
        print("\n  Liquidity-related values:")

        fields_to_check = (
            "last_price",
            "average_price",
            "volume",
            "average_traded_price",
            "buy_quantity",
            "sell_quantity",
            "ohlc",
            "net_change",
        )

        for field_name in fields_to_check:

            if field_name in quote:
                value = quote[field_name]

                # Avoid dumping large nested structures.
                if isinstance(value, dict):
                    print(f"    {field_name}: " f"{value}")
                else:
                    print(f"    {field_name}: " f"{value}")

        # -----------------------------------------------------------
        # 9. Calculate the value our current prefilter expects
        # -----------------------------------------------------------
        try:
            last_price = float(quote.get("last_price") or 0)

            average_price = float(quote.get("average_price") or 0)

            volume = float(quote.get("volume") or 0)

        except (TypeError, ValueError) as exc:
            print(f"\n  Could not convert liquidity fields: " f"{exc}")
            continue

        reference_price = average_price if average_price > 0 else last_price

        quote_traded_value = reference_price * volume

        print("\n  Calculated values:")

        print(f"    last_price          = " f"{last_price}")

        print(f"    average_price       = " f"{average_price}")

        print(f"    volume              = " f"{volume}")

        print(f"    reference_price     = " f"{reference_price}")

        print(f"    quote_traded_value   = " f"₹{quote_traded_value:,.2f}")

    # ---------------------------------------------------------------
    # 10. Diagnostic conclusion
    # ---------------------------------------------------------------
    print("\n" + "=" * 70)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 70)

    print("\nNo scanner files were modified.")

    print("No historical-data requests were made.")

    print("No orders were placed.")

    print("\nPlease send me the complete output from this test.")


if __name__ == "__main__":
    main()
