# engine/optimizer_gui_runner.py
import os
import config
from engine.data_loader import load_csv, validate_candles
from engine.optimizer import split_train_test, evaluate_results
from engine.trade_engine import TradeEngine
import pandas as pd
from engine.export_utils import save_results, export_optimizer_top_configs
from utils import calculate_drawdown_and_winrate

def run_optimizer_with_params(StrategyClass, progress_callback=None, per_result_callback=None):
    results = []
    test_id = 1

    for symbol in config.SYMBOLS:
        for interval in config.INTERVAL:
            df = load_csv(symbol, interval)
            if df is None or df.empty:
                continue

            if not validate_candles(df, interval=int(interval)):
                continue

            train_df, test_df = split_train_test(df, train_days=20, test_days=10)
            param_sets = list(StrategyClass.generate_param_combinations())

            for params in param_sets:
                # Train
                strat_train = StrategyClass(symbol, interval, train_df, params)
                strat_train.run()
                train_signals = strat_train.get_results()

                price_updates_train = [{
                    "timestamp": pd.to_datetime(row["timestamp"]),
                    "symbol": symbol,
                    "action": "price_update",
                    "price": row["close"],
                } for _, row in train_df.iterrows()]

                all_events_train = train_signals + price_updates_train
                all_events_train.sort(key=lambda x: x["timestamp"])

                trade_engine_train = TradeEngine(
                    starting_balance=config.START_BALANCE,
                    fee_pct=config.FEE_PCT,
                    slippage_pct=config.SLIPPAGE_PCT,
                    risk_per_trade=config.RISK_PCT
                )
                for event in all_events_train:
                    trade_engine_train.process_signal(event)
                train_trades = trade_engine_train.get_trades()
                train_balance = evaluate_results(train_trades, config.START_BALANCE)

                # Test
                strat_test = StrategyClass(symbol, interval, test_df, params)
                strat_test.run()
                test_signals = strat_test.get_results()

                price_updates_test = [{
                    "timestamp": pd.to_datetime(row["timestamp"]),
                    "symbol": symbol,
                    "action": "price_update",
                    "price": row["close"],
                } for _, row in test_df.iterrows()]

                all_events_test = test_signals + price_updates_test
                all_events_test.sort(key=lambda x: x["timestamp"])

                trade_engine_test = TradeEngine(
                    starting_balance=config.START_BALANCE,
                    fee_pct=config.FEE_PCT,
                    slippage_pct=config.SLIPPAGE_PCT,
                    risk_per_trade=config.RISK_PCT
                )
                for event in all_events_test:
                    trade_engine_test.process_signal(event)
                test_trades = trade_engine_test.get_trades()
                test_balance = evaluate_results(test_trades, config.START_BALANCE)

                max_drawdown, win_rate = calculate_drawdown_and_winrate(test_trades)

                result = {
                    "test_id": test_id,
                    "symbol": symbol,
                    "interval": interval,
                    **params,
                    "train_final_balance": round(train_balance, 2),
                    "test_final_balance": round(test_balance, 2),
                    "max_drawdown_pct": round(max_drawdown, 2),
                    "win_rate_pct": round(win_rate, 2)
                }

                results.append(result)
                test_id += 1

                if progress_callback:
                    progress_callback(test_id, len(param_sets))

                if per_result_callback:
                    per_result_callback(result)

    results.sort(key=lambda x: x["test_final_balance"], reverse=True)
    if results:
        os.makedirs("results", exist_ok=True)
        save_results(results, "results/optimizer_results.csv")
        export_optimizer_top_configs(results, "results/top_optimizer_configs.csv", top_n=10)

    return results
