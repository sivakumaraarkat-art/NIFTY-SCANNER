"""Inspect one Zerodha quote response without running the scanner."""

from configuration.swing_trade_settings import load_settings
from stock_universe.nse_stock_universe import load_nse_equity_universe
from zerodha_market_data.zerodha_connection import (
    create_zerodha_client,
    verify_connection,
)

SAFE_MARKET_FIELDS = {
    "average_price",
    "buy_quantity",
    "change",
    "close_price",
    "high",
    "last_price",
    "last_quantity",
    "last_trade_time",
    "low",
    "lower_circuit_limit",
    "ohlc",
    "open",
    "sell_quantity",
    "timestamp",
    "upper_circuit_limit",
    "volume",
}


def _field_names(value, prefix=""):
    """Return nested response field names without exposing response values."""
    names = []
    if isinstance(value, dict):
        for key, child in value.items():
            name = f"{prefix}.{key}" if prefix else str(key)
            names.append(name)
            names.extend(_field_names(child, name))
    elif isinstance(value, list) and value:
        names.extend(_field_names(value[0], f"{prefix}[]"))
    return names


def main():
    settings = load_settings()
    kite = create_zerodha_client(settings)
    verify_connection(kite)

    universe = load_nse_equity_universe(kite, settings)
    candidates = universe[:5]
    symbols = [candidate["tradingsymbol"] for candidate in candidates]

    if len(symbols) < 5:
        raise RuntimeError(
            f"Expected at least 5 stock candidates, found {len(symbols)}."
        )

    instruments = [f"NSE:{symbol}" for symbol in symbols]
    print(f"Requesting one quote batch for: {', '.join(symbols)}")
    quote_data = kite.quote(instruments)

    print("\nReturned quote keys and safe market values:")
    for instrument in instruments:
        quote = quote_data.get(instrument)
        print(f"\n{instrument}")

        if not quote:
            print("  No quote payload returned")
            continue

        print("  field_names:")
        for name in sorted(set(_field_names(quote))):
            print(f"    {name}")

        print("  safe_market_values:")
        for field in sorted(SAFE_MARKET_FIELDS):
            if field in quote:
                print(f"    {field}: {quote[field]!r}")


if __name__ == "__main__":
    main()
