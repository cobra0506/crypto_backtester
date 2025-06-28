import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from engine.data_loader import load_csv, validate_candles
from engine.strategies.example_strategy import ExampleStrategy  # <- switch strategy here

def run_strategy_for_symbol(symbol: str, interval: str, config: dict):
    df = load_csv(symbol, interval)
    if not validate_candles(df):
        print(f"❌ Invalid data for {symbol}, skipping.")
        return

    strategy = ExampleStrategy(symbol, interval, df, config)
    strategy.run()
    results = strategy.get_results()

    print(f"✅ Strategy complete for {symbol} — Trades: {len(results)}")
    for trade in results[:5]:  # print first few
        print(trade)

# ---------- TEST RUN ----------
if __name__ == "__main__":
    symbols = ["BTCUSDT"]  # Can expand to multi-symbol later
    interval = "1"
    config = {}  # Add strategy parameters here

    for symbol in symbols:
        run_strategy_for_symbol(symbol, interval, config)
