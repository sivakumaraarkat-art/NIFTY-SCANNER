from configuration.swing_trade_settings import load_settings
from zerodha_market_data.zerodha_connection import create_zerodha_client
from stock_universe.nse_stock_universe import load_nse_equity_universe
from stock_universe.liquid_stocks_universe import get_curated_liquid_symbols
from zerodha_market_data.market_data_downloader import HistoricalMarketDataDownloader
from stock_universe.liquidity_ranker import rank_liquid_stocks
from historical_market_data.technical_indicator_calculator import (
    add_technical_indicators,
)
from swing_strategies.swing_setup_engine import generate_setup_candidates
from trade_selection.swing_candidate_ranker import rank_trade_candidates

settings = load_settings()
client = create_zerodha_client(settings)
universe = load_nse_equity_universe(client, settings)

curated_symbols = get_curated_liquid_symbols()
candidate_map = {c["tradingsymbol"]: c for c in universe}
historical_candidates = [
    candidate_map[symbol] for symbol in curated_symbols[:226] if symbol in candidate_map
]

downloader = HistoricalMarketDataDownloader(client, settings)
data = downloader.download_universe(historical_candidates)

liquid_stocks = rank_liquid_stocks(
    data, minimum_average_traded_value=10_000_000, maximum_stocks=100
)
liquid_symbols = {item["symbol"] for item in liquid_stocks}
data = {symbol: df for symbol, df in data.items() if symbol in liquid_symbols}

frames = {}
for symbol, dataframe in data.items():
    try:
        frames[symbol] = add_technical_indicators(dataframe)
    except Exception as e:
        print(f"Error processing {symbol}: {e}")

candidates = generate_setup_candidates(frames, settings)
ranked = rank_trade_candidates(candidates, settings)

print("\n" + "=" * 60)
print("CURRENT SCAN: PRICE RANGE ANALYSIS")
print("=" * 60)
print(f"Total High-Conviction Signals Found: {len(ranked)}\n")

if ranked:
    prices = [c["entry"] for c in ranked]
    print("Price Statistics of Current Signals:")
    print(f"  • Lowest Price  : ₹{min(prices):,.2f}")
    print(f"  • Highest Price : ₹{max(prices):,.2f}")
    print(f"  • Average Price : ₹{sum(prices)/len(prices):,.2f}")
    print("\nDetailed List of Candidates:")
    for i, c in enumerate(ranked, 1):
        sym = c["symbol"]
        entry = c["entry"]
        setup = c["setup"]
        score = c["score"]
        qty = c.get("quantity", 0)
        cap = c.get("capital_required", 0)
        print(
            f"  {i}. {sym:<12} | Price: ₹{entry:>8,.2f} | Score: {score}/100 | Qty: {qty:>3} shares (₹{cap:>7,.0f}) | {setup}"
        )
print("=" * 60)
