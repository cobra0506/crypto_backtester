import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from engine.trade_engine import TradeEngine
from datetime import datetime, timezone

def run_tests():
    engine = TradeEngine(
        starting_balance=10000,
        fee_pct=0.001,
        slippage_pct=0.0005,
        risk_per_trade=0.01
    )

    # Open LONG then price updates hit TP auto-close
    engine.process_signal({"timestamp": datetime(2025,6,1,0,0,tzinfo=timezone.utc), "symbol": "BTCUSDT", "action": "open_long", "price": 100, "tp": 105, "sl": 95})
    engine.process_signal({"timestamp": datetime(2025,6,1,0,1,tzinfo=timezone.utc), "symbol": "BTCUSDT", "action": "price_update", "price": 102})
    engine.process_signal({"timestamp": datetime(2025,6,1,0,2,tzinfo=timezone.utc), "symbol": "BTCUSDT", "action": "price_update", "price": 106})  # Should auto-close at TP=105

    # Open SHORT then price updates hit SL auto-close
    engine.process_signal({"timestamp": datetime(2025,6,1,0,3,tzinfo=timezone.utc), "symbol": "ETHUSDT", "action": "open_short", "price": 200, "tp": 190, "sl": 210})
    engine.process_signal({"timestamp": datetime(2025,6,1,0,4,tzinfo=timezone.utc), "symbol": "ETHUSDT", "action": "price_update", "price": 209})
    engine.process_signal({"timestamp": datetime(2025,6,1,0,5,tzinfo=timezone.utc), "symbol": "ETHUSDT", "action": "price_update", "price": 211})  # Should auto-close at SL=210

    # Open LONG with trailing TP, price update moves trailing TP up, no close yet
    engine.process_signal({"timestamp": datetime(2025,6,1,0,6,tzinfo=timezone.utc), "symbol": "SOLUSDT", "action": "open_long", "price": 50, "trailing": {"pct": 0.02}})
    engine.process_signal({"timestamp": datetime(2025,6,1,0,7,tzinfo=timezone.utc), "symbol": "SOLUSDT", "action": "price_update", "price": 52})  # Trailing TP adjusts
    engine.process_signal({"timestamp": datetime(2025,6,1,0,8,tzinfo=timezone.utc), "symbol": "SOLUSDT", "action": "price_update", "price": 51})  # No close, price dropped but no TP/SL hit

    # Force close all remaining open positions
    engine.close_all(datetime(2025,6,1,0,9,tzinfo=timezone.utc), 51)

    # Print trades and summary
    print("\nTest Trade Log:")
    for t in engine.get_trades():
        print(t)

    print("\nTest Final Summary:")
    print(engine.get_summary())

if __name__ == "__main__":
    run_tests()
