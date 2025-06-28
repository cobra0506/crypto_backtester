import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engine.data_loader import load_csv, validate_candles
from engine.data_handler import fetch_and_save_candles
from engine.strategies.example_strategy import ExampleStrategy
import config
import pandas as pd
import time
from datetime import datetime, timedelta, timezone

class PortfolioManager:
    def __init__(self, starting_balance: float, fee_pct: float, slippage_pct: float):
        self.balance = starting_balance
        self.fee_pct = fee_pct
        self.slippage_pct = slippage_pct
        self.trade_log = []

    def process_trade(self, trade):
        # Apply slippage
        entry_price = trade["entry_price"] * (1 + self.slippage_pct)
        exit_price = trade["exit_price"] * (1 - self.slippage_pct)

        trade_size = 1  # simplify, can be improved

        gross_pnl = (exit_price - entry_price) * trade_size
        fee = (entry_price + exit_price) * trade_size * self.fee_pct
        net_pnl = gross_pnl - fee

        self.balance += net_pnl

        trade_record = trade.copy()
        trade_record.update({
            "net_pnl": net_pnl,
            "fee": fee,
            "balance_after": self.balance
        })
        self.trade_log.append(trade_record)

    def summary(self):
        return {
            "final_balance": self.balance,
            "total_trades": len(self.trade_log)
        }

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

def run_strategy_for_symbol_interval(symbol: str, interval: str, config_params: dict):
    if not ensure_data(symbol, interval):
        print(f"❌ Unable to get valid data for {symbol} interval {interval}m, skipping.")
        return []

    df = load_csv(symbol, interval)
    if not validate_candles(df, int(interval)):
        print(f"❌ Invalid data for {symbol} interval {interval}m, skipping.")
        return []

    strategy = ExampleStrategy(symbol, interval, df, config_params)
    strategy.run()
    return strategy.get_results()

if __name__ == "__main__":
    portfolio = PortfolioManager(
        starting_balance=config.START_BALANCE,
        fee_pct=config.FEE_PCT,
        slippage_pct=config.SLIPPAGE_PCT,
    )

    for symbol in config.SYMBOLS:
        for interval in config.INTERVAL:
            print(f"▶ Running strategy for {symbol} interval {interval}m")
            trades = run_strategy_for_symbol_interval(symbol, interval, {})
            print(f"→ {len(trades)} trades from {symbol} interval {interval}m")

            # Process all trades in the shared portfolio
            for trade in trades:
                portfolio.process_trade(trade)

    summary = portfolio.summary()
    print(f"\n🧾 Portfolio summary:")
    print(f"Starting balance: {config.START_BALANCE}")
    print(f"Final balance: {summary['final_balance']:.2f}")
    print(f"Total trades: {summary['total_trades']}")
