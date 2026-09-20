"""
STOCK SWING V1 - MASTER DRIVER

Executes the complete swing trade screening pipeline:
1. Load configuration
2. Verify Zerodha connection
3. Load full NSE equity universe
4. Stage 1: Fast quote-based liquidity prefilter across full universe
5. Download historical data with caching for top liquid candidates
6. Stage 2: Historical liquidity validation
7. Calculate technical indicators (SMA, EMA, RSI, ATR, Volume)
8. Generate swing trade setup candidates
9. Rank candidates and calculate risk/reward targets
10. Enrich candidates with Live Company News & Sentiment
11. Send Telegram alerts with FII/DII flow & News (signal-only mode)
"""

import os

from configuration.swing_trade_settings import load_settings
from zerodha_market_data.zerodha_connection import (
    create_zerodha_client,
    verify_connection,
)
from stock_universe.nse_stock_universe import load_nse_equity_universe
from stock_universe.liquidity_ranker import (
    prefilter_by_quote_liquidity,
    rank_liquid_stocks,
)
from zerodha_market_data.market_data_downloader import HistoricalMarketDataDownloader
from historical_market_data.technical_indicator_calculator import (
    add_technical_indicators,
)
from swing_strategies.swing_setup_engine import generate_setup_candidates
from trade_selection.swing_candidate_ranker import rank_trade_candidates
from news_analysis.company_news_analyzer import enrich_candidates_with_news
from telegram_alerts.swing_trade_alert_sender import send_swing_alerts
from stock_universe.controlled_stock_universe import (
    parse_controlled_symbols,
    select_controlled_universe,
)
from stock_universe.cap_classification import (
    classify_symbol_by_cap_segment,
    load_nse_cap_snapshot,
)


def build_controlled_candidate_universe(
    stock_candidates: list[dict],
    controlled_symbols: list[str],
    maximum_size: int,
) -> list[dict]:
    """Validate and return an explicit controlled universe in the source order."""
    requested_symbols = parse_controlled_symbols(",".join(controlled_symbols))
    return select_controlled_universe(
        stock_candidates=stock_candidates,
        controlled_symbols=requested_symbols,
        maximum_size=maximum_size,
    )


def main():
    settings = load_settings()
    print("STOCK SWING V1 - MASTER DRIVER\n")

    # ------------------------------------------------------------------
    # STAGE 1: CONFIGURATION
    # ------------------------------------------------------------------
    print("[1/9] Configuration loaded.")

    # ------------------------------------------------------------------
    # STAGE 2: ZERODHA CONNECTION
    # ------------------------------------------------------------------
    client = create_zerodha_client(settings)
    verify_connection(client)
    print("[2/9] Zerodha connection verified.")

    # ------------------------------------------------------------------
    # STAGE 3: UNIVERSE DISCOVERY (Full NSE Equity)
    # ------------------------------------------------------------------
    universe = load_nse_equity_universe(client, settings)
    controlled_symbol_source = os.getenv("CONTROLLED_SYMBOLS", "").strip()
    controlled_symbols = parse_controlled_symbols(controlled_symbol_source)

    if controlled_symbols:
        historical_pool = build_controlled_candidate_universe(
            stock_candidates=universe,
            controlled_symbols=controlled_symbols,
            maximum_size=max(1, settings.controlled_universe_size),
        )
        print(
            f"[3/9] Controlled universe selected: {len(historical_pool)} explicit "
            f"symbols from the validated NSE list."
        )
    else:
        historical_pool = universe
        print(f"[3/9] Stock candidates loaded: {len(universe)} symbols.")

    cap_snapshot = load_nse_cap_snapshot()
    cap_by_symbol = {}
    for candidate in historical_pool:
        symbol = str(candidate.get("tradingsymbol", "")).strip().upper()
        if symbol:
            cap_segment = classify_symbol_by_cap_segment(symbol, cap_snapshot)
            candidate["cap_segment"] = cap_segment
            cap_by_symbol[symbol] = cap_segment

    print(
        "[3/9] NSE cap segments: "
        + ", ".join(
            f"{segment}={sum(value == segment for value in cap_by_symbol.values())}"
            for segment in ("LARGE", "MID", "SMALL", "UNKNOWN")
        )
    )

    # ------------------------------------------------------------------
    # STAGE 4: STAGE 1 LIQUIDITY PREFILTER (Quote-based across full market)
    # ------------------------------------------------------------------
    # Prefilter the universe by current traded value using fast batched quote
    # requests. When a controlled symbol list is configured, the wholesale
    # selection is explicit and ordered; no arbitrary slice fallback is allowed.
    try:
        quote_liquid_candidates = prefilter_by_quote_liquidity(
            kite=client,
            stock_candidates=historical_pool,
            maximum_stocks=settings.max_historical_download_symbols,
            request_delay_seconds=1.10,
            minimum_price=settings.minimum_stock_price,
            maximum_price=settings.maximum_stock_price,
        )
        candidate_map = {c["tradingsymbol"]: c for c in historical_pool}
        historical_candidates = []
        for item in quote_liquid_candidates:
            sym = item.get("symbol") or item.get("tradingsymbol")
            if sym and sym in candidate_map:
                historical_candidates.append(candidate_map[sym])

        print(
            f"[4/9] Quote liquidity prefilter: selected {len(historical_candidates)} "
            f"top liquid stocks for historical download."
        )
    except Exception as exc:
        scope = "controlled" if controlled_symbols else "full-universe"
        raise RuntimeError(
            f"Quote prefilter failed for the {scope} scan: {exc}"
        ) from exc

    # ------------------------------------------------------------------
    # STAGE 5: HISTORICAL MARKET DATA DOWNLOAD (with caching)
    # ------------------------------------------------------------------
    downloader = HistoricalMarketDataDownloader(client, settings)
    data = downloader.download_universe(historical_candidates)
    print(f"[5/9] Historical market data ready: {len(data)} symbols.")

    # ------------------------------------------------------------------
    # STAGE 6: STAGE 2 HISTORICAL LIQUIDITY VALIDATION
    # ------------------------------------------------------------------
    liquid_stocks = rank_liquid_stocks(
        market_data=data,
        minimum_average_traded_value=10_000_000,  # 1 Crore daily avg turnover
        maximum_stocks=100,
        minimum_price=settings.minimum_stock_price,
        maximum_price=settings.maximum_stock_price,
    )
    liquid_symbols = {item["symbol"] for item in liquid_stocks}
    data = {symbol: df for symbol, df in data.items() if symbol in liquid_symbols}
    print(f"[6/9] Historical liquidity validated: {len(data)} stocks qualify.")

    # ------------------------------------------------------------------
    # STAGE 7: TECHNICAL INDICATORS
    # ------------------------------------------------------------------
    frames = {}
    for symbol, dataframe in data.items():
        try:
            frames[symbol] = add_technical_indicators(dataframe)
        except Exception as exc:
            print(f"WARNING: Indicator calculation failed for {symbol}: {exc}")

    print(f"[7/9] Technical indicators calculated for {len(frames)} symbols.")

    # ------------------------------------------------------------------
    # STAGE 8: STRATEGY SETUP GENERATION & RANKING
    # ------------------------------------------------------------------
    candidates = generate_setup_candidates(frames, settings)
    print(f"[8/9] Initial setup candidates: {len(candidates)}")

    ranked = rank_trade_candidates(candidates, settings)
    for candidate in ranked:
        symbol = str(candidate.get("symbol", "")).strip().upper()
        candidate["cap_segment"] = cap_by_symbol.get(symbol, "UNKNOWN")
    print(f"      Ranked high-conviction candidates: {len(ranked)}")

    # ------------------------------------------------------------------
    # STAGE 8.5: LIVE NEWS & CATALYST ENRICHMENT
    # ------------------------------------------------------------------
    if ranked:
        print(f"      Fetching news and sentiment for top {len(ranked)} candidates...")
        ranked = enrich_candidates_with_news(ranked)

    # ------------------------------------------------------------------
    # STAGE 9: NOTIFICATIONS (Telegram Alert with FII/DII + News)
    # ------------------------------------------------------------------
    send_swing_alerts(ranked, settings)
    print("[9/9] Telegram stage completed.\n")

    print("SCAN COMPLETE - SIGNAL ONLY / NO AUTOMATIC ORDERS")
    return ranked


if __name__ == "__main__":
    main()
