import os
import pandas as pd
import numpy as np
import itertools
import backtrader as bt

# === CONFIG ===
SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT"]
INTERVALS = ["1", "5", "15"]
START_BALANCE = 10000.0
FEE_PCT = 0.001
SLIPPAGE_PCT = 0.001
DATA_PATH = "data"
RESULTS_FILE = "optimizer_results_backtrader.csv"
TOP_RESULTS_FILE = "top_optimizer_configs_backtrader.csv"

# === STRATEGY ===
class MovingAverageCrossStrategy(bt.Strategy):
    params = dict(
        short_ma=5,
        long_ma=30,
        use_rsi_filter=True,
        rsi_period=14,
        rsi_oversold=30,
        rsi_overbought=70
    )

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.short_ma = bt.ind.SMA(period=self.p.short_ma)
        self.long_ma = bt.ind.SMA(period=self.p.long_ma)
        self.rsi = bt.ind.RSI(period=self.p.rsi_period) if self.p.use_rsi_filter else None
        self.order = None

    def next(self):
        if self.order:
            return  # waiting for order

        if not self.position:
            if self.short_ma[0] > self.long_ma[0] and self.short_ma[-1] <= self.long_ma[-1]:
                if self.p.use_rsi_filter and self.rsi and self.rsi[0] > self.p.rsi_oversold:
                    return
                self.order = self.buy()
        else:
            if self.short_ma[0] < self.long_ma[0] and self.short_ma[-1] >= self.long_ma[-1]:
                self.order = self.sell()

# === PARAMETER GRID ===
param_grid = list(itertools.product(
    [5, 10, 20],  # short_ma
    [30, 50, 100],  # long_ma
    [True, False],  # use_rsi_filter
    [14],  # rsi_period
    [30],  # rsi_oversold
    [70],  # rsi_overbought
))

# === OPTIMIZATION RUNNER ===
results = []
test_id = 1

for symbol in SYMBOLS:
    for interval in INTERVALS:
        file_path = os.path.join(DATA_PATH, f"{symbol}_{interval}m.csv")
        if not os.path.exists(file_path):
            continue
        df = pd.read_csv(file_path, parse_dates=["timestamp"])
        df = df[["timestamp", "open", "high", "low", "close", "volume"]]
        df.columns = ["datetime", "open", "high", "low", "close", "volume"]
        df.set_index("datetime", inplace=True)
        df = df.tz_convert("UTC") if df.index.tz is not None else df.tz_localize("UTC")

        for short_ma, long_ma, use_rsi, rsi_period, rsi_oversold, rsi_overbought in param_grid:
            if short_ma >= long_ma:
                continue

            print(f"Running test {test_id} — Symbol: {symbol}, Interval: {interval}m, Params: SMA({short_ma}, {long_ma}), RSI: {use_rsi}")

            cerebro = bt.Cerebro()
            cerebro.broker.setcash(START_BALANCE)
            cerebro.broker.setcommission(commission=FEE_PCT + SLIPPAGE_PCT)

            data = bt.feeds.PandasData(dataname=df)
            cerebro.adddata(data)

            cerebro.addstrategy(
                MovingAverageCrossStrategy,
                short_ma=short_ma,
                long_ma=long_ma,
                use_rsi_filter=use_rsi,
                rsi_period=rsi_period,
                rsi_oversold=rsi_oversold,
                rsi_overbought=rsi_overbought
            )

            starting_value = cerebro.broker.getvalue()
            cerebro.run()
            ending_value = cerebro.broker.getvalue()
            balance_diff = ending_value - starting_value
            pct_return = (ending_value / starting_value - 1) * 100

            results.append({
                "test_id": test_id,
                "symbol": symbol,
                "interval": interval,
                "short_ma": short_ma,
                "long_ma": long_ma,
                "use_rsi_filter": use_rsi,
                "rsi_period": rsi_period,
                "rsi_oversold": rsi_oversold,
                "rsi_overbought": rsi_overbought,
                "train_final_balance": START_BALANCE,  # No split yet
                "test_final_balance": round(ending_value, 2),
                "max_drawdown_pct": 0.0,  # Simplified, no equity curve tracked
                "win_rate_pct": 0.0,  # Placeholder
            })
            test_id += 1

# Save results
results_df = pd.DataFrame(results)
results_df.to_csv(RESULTS_FILE, index=False)

top_df = results_df.sort_values("test_final_balance", ascending=False).head(10)
top_df.to_csv(TOP_RESULTS_FILE, index=False)

RESULTS_FILE, TOP_RESULTS_FILE
