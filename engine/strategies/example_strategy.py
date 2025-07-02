# example_strategy.py

from engine.strategy_interface import BaseStrategy
import itertools
import pandas as pd

class ExampleStrategy(BaseStrategy):
    # Param grid inside the strategy for optimizer use
    param_grid = {
        "entry_interval": [5, 10, 15],
        "exit_offset": [3, 5, 7]
    }

    def __init__(self, symbol, interval, data, params=None):
        import config  # or pass config from outside
        super().__init__(symbol, interval, data, config)
        self.params = params or {}
        self.entry_interval = self.params.get("entry_interval", 10)
        self.exit_offset = self.params.get("exit_offset", 5)
        self.trades = []

    def run(self):
        self.signals = []
        directions = ["LONG", "SHORT"]
        dir_idx = 0

        for i in range(0, len(self.data) - self.exit_offset, self.entry_interval):
            entry = self.data.iloc[i]
            exit_ = self.data.iloc[i + self.exit_offset]
            direction = directions[dir_idx % 2]
            dir_idx += 1

            # Entry signal
            self.signals.append({
                "timestamp": pd.to_datetime(entry["timestamp"]),
                "symbol": self.symbol,
                "direction": direction,
                "entry_price": entry["close"],
                "take_profit": entry["close"] * (1.02 if direction == "LONG" else 0.98),
                "stop_loss": entry["close"] * (0.98 if direction == "LONG" else 1.02),
            })

            # Exit signal
            self.signals.append({
                "timestamp": pd.to_datetime(exit_["timestamp"]),
                "symbol": self.symbol,
                "exit": True,
                "exit_price": exit_["close"],
            })

    def get_results(self):
        return self.signals  # ✅ Send signals to trade engine

    @classmethod
    def generate_param_combinations(cls):
        keys = cls.param_grid.keys()
        values = cls.param_grid.values()
        for combination in itertools.product(*values):
            yield dict(zip(keys, combination))
