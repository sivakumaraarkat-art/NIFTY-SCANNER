"""Refresh official NSE large-, mid-, and small-cap constituent snapshots."""

from datetime import date
import csv
import io
import json
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "data" / "nse_cap_segments"
SOURCES = {
    "LARGE": (
        "nifty100.csv",
        "https://www.niftyindices.com/IndexConstituent/ind_nifty100list.csv",
    ),
    "MID": (
        "nifty_midcap150.csv",
        "https://www.niftyindices.com/IndexConstituent/ind_niftymidcap150list.csv",
    ),
    "SMALL": (
        "nifty_smallcap250.csv",
        "https://www.niftyindices.com/IndexConstituent/ind_niftysmallcap250list.csv",
    ),
}


def download_symbols(url):
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=30) as response:
        text = response.read().decode("utf-8-sig")
    rows = csv.DictReader(io.StringIO(text))
    symbols = []
    for row in rows:
        symbol = str(row.get("Symbol", "")).strip().upper()
        series = str(row.get("Series", "")).strip().upper()
        if symbol and series == "EQ" and symbol not in symbols:
            symbols.append(symbol)
    if not symbols:
        raise RuntimeError(f"No EQ symbols received from {url}")
    return symbols


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    counts = {}
    for segment, (filename, url) in SOURCES.items():
        symbols = download_symbols(url)
        with (OUTPUT / filename).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["symbol"])
            writer.writeheader()
            writer.writerows({"symbol": symbol} for symbol in symbols)
        counts[segment] = len(symbols)
    metadata = {
        "snapshot_date": date.today().isoformat(),
        "source": "NSE index constituent snapshot downloaded from niftyindices.com",
        "files": {segment: filename for segment, (filename, _) in SOURCES.items()},
        "counts": counts,
    }
    (OUTPUT / "metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    print(metadata)


if __name__ == "__main__":
    main()
