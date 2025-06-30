import os
import sys
import csv
import pandas as pd
from datetime import datetime, timedelta, timezone
sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # Add project root to sys.path
import config
from utils import load_class_from_string
from engine.data_loader import load_csv, validate_candles

def split_train_test(df, train_days=20, test_days=10):
    """Split DataFrame into train and test by date."""
    if df.empty:
        return None, None
    end_date = pd.to_datetime(df["timestamp"].iloc[-1], utc=True)
    train_start = end_date - pd.Timedelta(days=train_days + test_days)
    train_end = end_date - pd.Timedelta(days=test_days)
    train_df = df[(df["timestamp"] >= train_start.isoformat()) & (df["timestamp"] < train_end.isoformat())]
    test_df = df[(df["timestamp"] >= train_end.isoformat()) & (df["timestamp"] <= end_date.isoformat())]
    return train_df.reset_index(drop=True), test_df.reset_index(drop=True)

def evaluate_results(trades, starting_balance):
    """Calculate final balance after trades."""
    balance = starting_balance
    for trade in trades:
        balance += trade.get("net_pnl", 0)
    return balance

def save_results(results, filename="optimizer_results.csv"):
    """Save list of dict results to CSV."""
    if not results:
        print("No results to save.")
        return
    keys = results[0].keys()
    with open(filename, "w", newline="", encoding="utf-8") as f:
        dict_writer = csv.DictWriter(f, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(results)
    print(f"Saved optimizer results to {filename}")

def main():
    StrategyClass = load_class_from_string(config.STRATEGY_CLASS)

    symbol = config.SYMBOLS[0]
    interval = config.INTERVAL[0]

    print(f"Loading data for {symbol} interval {interval}m")
    df = load_csv(symbol, interval)
    if df is None or df.empty:
        print("No data loaded, aborting.")
        return

    if not validate_candles(df, interval=int(interval)):
        print("Data validation failed, aborting.")
        return

    train_df, test_df = split_train_test(df, train_days=20, test_days=10)
    if train_df is None or test_df is None:
        print("Train/test split failed, aborting.")
        return

    param_sets = list(StrategyClass.generate_param_combinations())
    print(f"Running optimization with {len(param_sets)} parameter sets...")

    results = []

    for idx, params in enumerate(param_sets, 1):
        strat_train = StrategyClass(symbol, interval, train_df, params)
        strat_train.run()
        train_trades = strat_train.get_results()
        train_final_balance = evaluate_results(train_trades, config.START_BALANCE)

        strat_test = StrategyClass(symbol, interval, test_df, params)
        strat_test.run()
        test_trades = strat_test.get_results()
        test_final_balance = evaluate_results(test_trades, config.START_BALANCE)

        results.append({
            **params,
            "train_final_balance": train_final_balance,
            "test_final_balance": test_final_balance
        })

        print(f"[{idx}/{len(param_sets)}] Params: {params} | Train Bal: {train_final_balance:.2f} | Test Bal: {test_final_balance:.2f}")

    results.sort(key=lambda x: x["test_final_balance"], reverse=True)

    print("\nTop 10 parameter sets by test final balance:")
    for r in results[:10]:
        print(r)

    # Save all results CSV
    save_results(results)

    # ===== Add exports here =====
    from engine.export_utils import export_optimizer_top_configs
    export_optimizer_top_configs(results, "top_optimizer_configs.csv", top_n=10)

    print("Optimization complete, results exported.")

if __name__ == "__main__":
    main()
