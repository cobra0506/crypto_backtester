# engin/strategies/MovingAverageCrossStrategy.py
import pandas as pd
import numpy as np
from engine.strategy_interface import BaseStrategy
import itertools

class MovingAverageCrossStrategy(BaseStrategy):
    param_grid = {
        "short_ma": [5, 10, 20],
        "long_ma": [30, 50, 100],
        "use_rsi_filter": [True, False],
        "rsi_period": [14],
        "rsi_oversold": [30],
        "rsi_overbought": [70],
    }

    def __init__(self, symbol, interval, data, params=None):
        import config
        super().__init__(symbol, interval, data, config)
        self.signals = []
        self.params = params or {}
        self.trades = []

    @classmethod
    def generate_param_combinations(cls):
        keys = cls.param_grid.keys()
        vals = cls.param_grid.values()
        for combo in itertools.product(*vals):
            combo_dict = dict(zip(keys, combo))
            if combo_dict["short_ma"] >= combo_dict["long_ma"]:
                continue  # Invalid combo
            yield combo_dict

    def run(self):
        df = self.data.copy()
        short = self.params["short_ma"]
        long = self.params["long_ma"]
        use_rsi = self.params["use_rsi_filter"]
        rsi_period = self.params["rsi_period"]

        df["short_ma"] = df["close"].rolling(window=short).mean()
        df["long_ma"] = df["close"].rolling(window=long).mean()

        if use_rsi:
            delta = df["close"].diff()
            gain = delta.clip(lower=0)
            loss = -delta.clip(upper=0)
            avg_gain = gain.rolling(window=rsi_period).mean()
            avg_loss = loss.rolling(window=rsi_period).mean()
            rs = avg_gain / avg_loss
            df["rsi"] = 100 - (100 / (1 + rs))
        else:
            df["rsi"] = np.nan  # Placeholder

        in_position = False
        for i in range(1, len(df)):
            row = df.iloc[i]
            prev = df.iloc[i - 1]

            if np.isnan(row["short_ma"]) or np.isnan(row["long_ma"]):
                continue

            if not in_position:
                # Buy condition
                if (
                    prev["short_ma"] < prev["long_ma"]
                    and row["short_ma"] > row["long_ma"]
                ):
                    if use_rsi and not np.isnan(row["rsi"]) and row["rsi"] > self.params["rsi_oversold"]:
                        continue
                    self.signals.append({
                        "timestamp": row["timestamp"],
                        "symbol": self.symbol,
                        "direction": "LONG",
                        "entry_price": row["close"],
                        "take_profit": row["close"] * 1.02,
                        "stop_loss": row["close"] * 0.98,
                    })
                    in_position = True
            else:
                # Sell condition
                if (
                    prev["short_ma"] > prev["long_ma"]
                    and row["short_ma"] < row["long_ma"]
                ):
                    self.signals.append({
                        "timestamp": row["timestamp"],
                        "symbol": self.symbol,
                        "exit": True,
                        "exit_price": row["close"]
                    })
                    in_position = False

    def get_results(self):
        return self.signals
