# example_strategy.py

from engine.strategy_interface import BaseStrategy
import itertools

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
        self.trades.clear()
        directions = ["LONG", "SHORT"]
        dir_idx = 0

        for i in range(0, len(self.data) - self.exit_offset, self.entry_interval):
            entry = self.data.iloc[i]
            exit_ = self.data.iloc[i + self.exit_offset]
            direction = directions[dir_idx % 2]
            dir_idx += 1

            pnl = (exit_["close"] - entry["close"]) if direction == "LONG" else (entry["close"] - exit_["close"])
            fee = abs(pnl) * 0.0005  # Example 0.05% fee
            slippage = abs(pnl) * 0.00025  # Example slippage
            net_pnl = pnl - fee - slippage

            self.trades.append({
                "symbol": self.symbol,
                "direction": direction,
                "entry_time": entry["timestamp"],
                "entry_price": entry["close"],
                "exit_time": exit_["timestamp"],
                "exit_price": exit_["close"],
                "pnl": pnl,
                "fee": fee,
                "slippage": slippage,
                "net_pnl": net_pnl,
            })


    def get_results(self):
        return self.trades

    @classmethod
    def generate_param_combinations(cls):
        keys = cls.param_grid.keys()
        values = cls.param_grid.values()
        for combination in itertools.product(*values):
            yield dict(zip(keys, combination))
