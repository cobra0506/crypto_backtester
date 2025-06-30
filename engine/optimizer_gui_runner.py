import config
from engine.data_loader import load_csv, validate_candles
from engine.optimizer import split_train_test, evaluate_results

def run_optimizer_with_params(StrategyClass, symbol, interval, progress_callback=None):
    df = load_csv(symbol, interval)
    if df is None or df.empty:
        return []

    if not validate_candles(df, interval=int(interval)):
        return []

    train_df, test_df = split_train_test(df, train_days=20, test_days=10)
    param_sets = list(StrategyClass.generate_param_combinations())
    results = []

    for idx, params in enumerate(param_sets, 1):
        strat_train = StrategyClass(symbol, interval, train_df, params)
        strat_train.run()
        train_trades = strat_train.get_results()
        train_balance = evaluate_results(train_trades, config.START_BALANCE)

        strat_test = StrategyClass(symbol, interval, test_df, params)
        strat_test.run()
        test_trades = strat_test.get_results()
        test_balance = evaluate_results(test_trades, config.START_BALANCE)

        results.append({
            **params,
            "train_final_balance": train_balance,
            "test_final_balance": test_balance
        })

        if progress_callback:
            progress_callback(idx, len(param_sets))

    results.sort(key=lambda x: x["test_final_balance"], reverse=True)
    return results
