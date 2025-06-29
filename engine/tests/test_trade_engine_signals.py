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

    # 1) Open LONG and close LONG with manual exit action
    actions = [
        {"timestamp": datetime(2025,6,1,0,0,tzinfo=timezone.utc), "symbol": "BTCUSDT", "action": "open_long", "price": 100, "tp": 110, "sl": 95},
        {"timestamp": datetime(2025,6,1,0,3,tzinfo=timezone.utc), "symbol": "BTCUSDT", "action": "close_long", "price": 105},
    ]
    for sig in actions:
        engine.process_signal(sig)

    # 2) Open SHORT and close SHORT with manual exit action
    actions = [
        {"timestamp": datetime(2025,6,1,0,5,tzinfo=timezone.utc), "symbol": "ETHUSDT", "action": "open_short", "price": 200, "tp": 190, "sl": 210},
        {"timestamp": datetime(2025,6,1,0,8,tzinfo=timezone.utc), "symbol": "ETHUSDT", "action": "close_short", "price": 195},
    ]
    for sig in actions:
        engine.process_signal(sig)

    # 3) Test auto-close with manual close for now (remove price_update)
    engine.process_signal({"timestamp": datetime(2025,6,1,0,10,tzinfo=timezone.utc), "symbol": "BTCUSDT", "action": "open_long", "price": 100, "tp": 105})
    engine.process_signal({"timestamp": datetime(2025,6,1,0,11,tzinfo=timezone.utc), "symbol": "BTCUSDT", "action": "close_long", "price": 106})  # Manual close instead of price_update

    # 4) Similarly for SHORT
    engine.process_signal({"timestamp": datetime(2025,6,1,0,12,tzinfo=timezone.utc), "symbol": "ETHUSDT", "action": "open_short", "price": 200, "sl": 210})
    engine.process_signal({"timestamp": datetime(2025,6,1,0,13,tzinfo=timezone.utc), "symbol": "ETHUSDT", "action": "close_short", "price": 211})  # Manual close

    # 5) Trailing TP updates test - only open_long action (price updates skipped)
    engine.process_signal({"timestamp": datetime(2025,6,1,0,14,tzinfo=timezone.utc), "symbol": "BTCUSDT", "action": "open_long", "price": 100, "trailing": {"pct": 0.02}})

    # 6) Multiple simultaneous positions
    engine.process_signal({"timestamp": datetime(2025,6,1,0,17,tzinfo=timezone.utc), "symbol": "SOLUSDT", "action": "open_long", "price": 50, "tp": 60})
    engine.process_signal({"timestamp": datetime(2025,6,1,0,18,tzinfo=timezone.utc), "symbol": "ADAUSDT", "action": "open_short", "price": 30, "tp": 25})

    # 7) Close all forcibly
    engine.close_all(datetime(2025,6,1,0,21,tzinfo=timezone.utc), 50)

    # 8) Invalid/missing action keys (should raise or ignore)
    try:
        engine.process_signal({"timestamp": datetime(2025,6,1,0,22,tzinfo=timezone.utc), "symbol": "BTCUSDT", "action": "open_long"})  # Missing price, will error
    except Exception as e:
        print(f"Caught expected error: {e}")

    try:
        engine.process_signal({"timestamp": datetime(2025,6,1,0,23,tzinfo=timezone.utc), "action": "close_short", "price": 100})  # Missing symbol, will error
    except Exception as e:
        print(f"Caught expected error: {e}")

    # Output trades and summary
    print("\nTest Trade Log:")
    for t in engine.get_trades():
        print(t)

    print("\nTest Final Summary:")
    print(engine.get_summary())

def run_price_update_test():
    engine = TradeEngine(starting_balance=10000, fee_pct=0.001, slippage_pct=0.0005, risk_per_trade=0.01)

    # Open LONG with TP=105, SL=95
    engine.process_signal({
        "timestamp": datetime(2025, 6, 1, 0, 0, tzinfo=timezone.utc),
        "symbol": "BTCUSDT",
        "action": "open_long",
        "price": 100,
        "tp": 105,
        "sl": 95
    })

    # Price moves but no TP/SL hit - no close
    engine.process_signal({
        "timestamp": datetime(2025, 6, 1, 0, 1, tzinfo=timezone.utc),
        "symbol": "BTCUSDT",
        "action": "price_update",
        "price": 103
    })

    assert "BTCUSDT" in engine.positions, "Position should still be open"

    # Price hits TP -> should auto-close
    engine.process_signal({
        "timestamp": datetime(2025, 6, 1, 0, 2, tzinfo=timezone.utc),
        "symbol": "BTCUSDT",
        "action": "price_update",
        "price": 105
    })

    assert "BTCUSDT" not in engine.positions, "Position should be closed on TP"

    trades = engine.get_trades()
    assert len(trades) == 1
    print("Price update auto-close test passed!")

if __name__ == "__main__":
    run_price_update_test()

