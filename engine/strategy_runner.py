#startegy_runner.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engine.data_loader import load_csv, validate_candles
from engine.data_handler import fetch_and_save_candles
from engine.strategies.example_strategy import ExampleStrategy
from engine.trade_engine import TradeEngine  # <-- NEW
import config
import pandas as pd
import time
from datetime import datetime, timedelta, timezone


def ensure_data(symbol: str, interval: str) -> bool:
    filename = f"data/{symbol}_{interval}m.csv"
    if not os.path.isfile(filename):
        print(f"❌ File not found: {filename}")
        print(f"⬇️ Downloading missing data for {symbol} interval {interval}m...")
        success = fetch_and_save_candles(symbol, interval, config.HISTORICAL_DAYS)
        if success:
            time.sleep(1)
        return success

    df = load_csv(symbol, interval)
    if df is None or df.empty:
        print(f"❌ DataFrame empty or None for {filename}")
        print(f"⬇️ Re-downloading corrupted data for {symbol} interval {interval}m...")
        success = fetch_and_save_candles(symbol, interval, config.HISTORICAL_DAYS)
        if success:
            time.sleep(1)
        return success

    required_start = datetime.now(timezone.utc) - timedelta(days=config.HISTORICAL_DAYS)
    first_timestamp = pd.to_datetime(df["timestamp"].iloc[0], utc=True)

    if first_timestamp > required_start:
        print(f"❌ Data too short for {symbol} interval {interval}m ({first_timestamp} > {required_start})")
        print(f"⬇️ Downloading missing data for {symbol} interval {interval}m...")
        success = fetch_and_save_candles(symbol, interval, config.HISTORICAL_DAYS)
        if success:
            time.sleep(1)
        return success

    return True


def run_strategy_for_symbol_interval(symbol: str, interval: str, trade_engine: TradeEngine, config_params: dict):
    if not ensure_data(symbol, interval):
        print(f"❌ Unable to get valid data for {symbol} interval {interval}m, skipping.")
        return

    df = load_csv(symbol, interval)
    if not validate_candles(df, interval=int(interval)):
        print(f"❌ Invalid data for {symbol} interval {interval}m, skipping.")
        return

    strategy = ExampleStrategy(symbol, interval, df, config_params)
    strategy.run()

    # Strategy now produces entry/exit signals in strategy.signals
    strategy_signals = strategy.signals  # Make sure `run()` populates this list

    # Create price update signals per candle
    price_updates = [{
        "timestamp": pd.to_datetime(row["timestamp"]),
        "symbol": symbol,
        "action": "price_update",
        "price": row["close"],
    } for _, row in df.iterrows()]

    # Combine all signals and price updates
    all_events = strategy_signals + price_updates

    # Sort by timestamp
    all_events.sort(key=lambda x: x["timestamp"])

    # Feed all events to the TradeEngine in chronological order
    for event in all_events:
        try:
            trade_engine.process_signal(event)
        except Exception as e:
            print(f"⚠️ Error processing event: {event}\n{e}")


if __name__ == "__main__":
    trade_engine = TradeEngine(
        starting_balance=config.START_BALANCE,
        fee_pct=config.FEE_PCT,
        slippage_pct=config.SLIPPAGE_PCT,
        risk_per_trade=config.RISK_PCT
    )

    for symbol in config.SYMBOLS:
        for interval in config.INTERVAL:
            print(f"▶ Running strategy for {symbol} interval {interval}m")
            run_strategy_for_symbol_interval(symbol, interval, trade_engine, {})

    summary = trade_engine.get_summary()
    print(f"\n🧾 Portfolio summary:")
    print(f"Starting balance: {config.START_BALANCE}")
    print(f"Final balance: {summary['final_balance']:.2f}")
    print(f"Total trades: {summary['total_trades']}")
    print(f"Max drawdown: {summary['max_drawdown_pct']:.2f}%")
