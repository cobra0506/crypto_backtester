# walk_forward_optimizer.py
import os
import sys
import pandas as pd
from datetime import datetime, timedelta, timezone
from engine.export_utils import save_results

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config
from engine.data_loader import load_csv, validate_candles
from engine.data_handler import fetch_and_save_candles
from engine.export_utils import export_optimizer_top_configs
from engine.trade_engine import TradeEngine
from engine.strategies.example_strategy import ExampleStrategy

def split_train_test(df, train_days=20, test_days=10):
    """Split DataFrame into train and test segments by date."""
    if df.empty:
        return None, None
    end_date = pd.to_datetime(df["timestamp"].iloc[-1], utc=True)
    train_start = end_date - pd.Timedelta(days=train_days + test_days)
    train_end = end_date - pd.Timedelta(days=test_days)
    train_df = df[(df["timestamp"] >= train_start.isoformat()) & (df["timestamp"] < train_end.isoformat())]
    test_df = df[(df["timestamp"] >= train_end.isoformat()) & (df["timestamp"] <= end_date.isoformat())]
    return train_df.reset_index(drop=True), test_df.reset_index(drop=True)

def ensure_data(symbol: str, interval: str) -> bool:
    filename = f"data/{symbol}_{interval}m.csv"
    if not os.path.isfile(filename):
        print(f"❌ File not found: {filename}")
        print(f"⬇️ Downloading missing data for {symbol} interval {interval}m...")
        success = fetch_and_save_candles(symbol, interval, config.HISTORICAL_DAYS)
        return success

    df = load_csv(symbol, interval)
    if df is None or df.empty:
        print(f"❌ Data empty or None for {filename}")
        print(f"⬇️ Re-downloading corrupted data for {symbol} interval {interval}m...")
        success = fetch_and_save_candles(symbol, interval, config.HISTORICAL_DAYS)
        return success

    required_start = datetime.now(timezone.utc) - timedelta(days=config.HISTORICAL_DAYS)
    first_timestamp = pd.to_datetime(df["timestamp"].iloc[0], utc=True)

    if first_timestamp > required_start:
        print(f"❌ Data too short for {symbol} interval {interval}m ({first_timestamp} > {required_start})")
        print(f"⬇️ Downloading missing data for {symbol} interval {interval}m...")
        success = fetch_and_save_candles(symbol, interval, config.HISTORICAL_DAYS)
        return success

    return True

def run_walk_forward_optimization(symbol: str, interval: str):
    print(f"▶ Starting walk-forward optimization for {symbol} {interval}m")

    if not ensure_data(symbol, interval):
        print(f"❌ Unable to get data for {symbol} interval {interval}m, skipping.")
        return []

    df = load_csv(symbol, interval)
    if df is None or df.empty:
        print(f"❌ Loaded data empty or None for {symbol} interval {interval}m, skipping.")
        return []

    if not validate_candles(df, interval=int(interval)):
        print(f"❌ Candle data validation failed for {symbol} interval {interval}m, skipping.")
        return []

    # Use config.HISTORICAL_DAYS to split train/test (e.g. 2/3 train, 1/3 test)
    total_days = config.HISTORICAL_DAYS
    train_days = int(total_days * 2 / 3)
    test_days = total_days - train_days

    train_df, test_df = split_train_test(df, train_days=train_days, test_days=test_days)
    if train_df is None or test_df is None or train_df.empty or test_df.empty:
        print(f"❌ Not enough data ({len(df)} rows) for train+test split ({train_days}+{test_days} days) on {symbol} {interval}m")
        return []

    param_sets = list(ExampleStrategy.generate_param_combinations())
    print(f"Running walk-forward optimization for {symbol} {interval}m with {len(param_sets)} parameter sets...")

    results = []

    for idx, params in enumerate(param_sets, 1):
        # Train
        strat_train = ExampleStrategy(symbol, interval, train_df, params)
        strat_train.run()
        trade_engine_train = TradeEngine(
            starting_balance=config.START_BALANCE,
            fee_pct=config.FEE_PCT,
            slippage_pct=config.SLIPPAGE_PCT,
            risk_per_trade=config.RISK_PCT
        )
        for event in strat_train.signals + price_update_events(train_df, symbol):
            trade_engine_train.process_signal(event)

        train_final_balance = trade_engine_train.balance
        train_trades = trade_engine_train.get_trades()
        train_equity_curve = build_equity_curve(train_trades, config.START_BALANCE)

        # Test
        strat_test = ExampleStrategy(symbol, interval, test_df, params)
        strat_test.run()
        trade_engine_test = TradeEngine(
            starting_balance=config.START_BALANCE,
            fee_pct=config.FEE_PCT,
            slippage_pct=config.SLIPPAGE_PCT,
            risk_per_trade=config.RISK_PCT
        )
        for event in strat_test.signals + price_update_events(test_df, symbol):
            trade_engine_test.process_signal(event)

        test_final_balance = trade_engine_test.balance
        test_trades = trade_engine_test.get_trades()
        test_equity_curve = build_equity_curve(test_trades, config.START_BALANCE)

        win_rate = calc_win_rate(test_trades)
        max_drawdown = calc_max_drawdown(test_trades)

        results.append({
            "test_id": idx,
            **params,
            "train_final_balance": round(train_final_balance, 2),
            "test_final_balance": round(test_final_balance, 2),
            "train_total_trades": len(train_trades),
            "test_total_trades": len(test_trades),
            "win_rate": win_rate,
            "max_drawdown": round(max_drawdown, 2),
            "train_equity_curve": train_equity_curve,
            "test_equity_curve": test_equity_curve
        })

        print(f"[{idx}/{len(param_sets)}] Params: {params} | Train Bal: {train_final_balance:.2f} | Test Bal: {test_final_balance:.2f} | Trades (Train/Test): {len(train_trades)}/{len(test_trades)}")

    return results


# Helper to convert candle DataFrame to price update events
def price_update_events(df, symbol):
    return [{
        "timestamp": pd.to_datetime(row["timestamp"]),
        "symbol": symbol,
        "action": "price_update",
        "price": row["close"],
    } for _, row in df.iterrows()]


# Build equity curve from trades
def build_equity_curve(trades, start_balance):
    equity = start_balance
    equity_curve = []
    trades_sorted = sorted(trades, key=lambda t: t["exit_time"] if "exit_time" in t else t["timestamp"])
    for trade in trades_sorted:
        equity += trade.get("net_pnl", 0)
        equity_curve.append({"timestamp": trade.get("exit_time", trade.get("timestamp")), "equity": equity})
    return equity_curve


# Calculate win rate
def calc_win_rate(trades):
    wins = [t for t in trades if t.get("net_pnl", 0) > 0]
    return round(len(wins) / len(trades), 4) if trades else 0


# Calculate max drawdown from trades
def calc_max_drawdown(trades):
    equity = 0
    peak = 0
    drawdown = 0
    for t in trades:
        equity += t.get("net_pnl", 0)
        if equity > peak:
            peak = equity
        dd = peak - equity
        if dd > drawdown:
            drawdown = dd
    return drawdown


def main():
    all_results = []

    os.makedirs("results", exist_ok=True)

    for symbol in config.SYMBOLS:
        for interval in config.INTERVAL:
            results = run_walk_forward_optimization(symbol, interval, train_days=20, test_days=10)
            all_results.extend(results)

    if not all_results:
        print("No walk-forward results to save.")
        return

    # Sort by best test final balance
    all_results.sort(key=lambda x: x["test_final_balance"], reverse=True)

    print("\nTop 10 optimizer configs by test final balance:")
    for r in all_results[:10]:
        print({
            "entry_interval": r["entry_interval"],
            "exit_offset": r["exit_offset"],
            "test_final_balance": float(r["test_final_balance"]),
            "train_final_balance": float(r["train_final_balance"]),
            "test_total_trades": r["test_total_trades"],
            "train_total_trades": r["train_total_trades"]
        })

    export_optimizer_top_configs(all_results, "results/top_optimizer_configs.csv", top_n=10)
    print("Walk-forward optimization complete. Top results saved.")
    
    save_results(all_results, "results/optimizer_results.csv")  # Full param set results

    # Optional: Create a very basic summary
    summary = {
        "total_tests": len(all_results),
        "best_test_balance": all_results[0]["test_final_balance"],
        "best_params": {k: all_results[0][k] for k in all_results[0] if k in ExampleStrategy.param_grid}
    }
    #export_summary_to_csv(summary, "summary.csv")


if __name__ == "__main__":
    main()
