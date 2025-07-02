# engine/strategies/RSIMovingAverageStrategy.py
from engine.strategy_interface import BaseStrategy
import pandas as pd
import numpy as np

class RSIMovingAverageStrategy(BaseStrategy):
    param_grid = {
        "rsi_period": [14],
        "rsi_overbought": [70],
        "rsi_oversold": [30],
        "ma_period": [20, 50],
    }

    def __init__(self, symbol, interval, data, params=None):
        import config
        super().__init__(symbol, interval, data, config)
        self.params = params or {}
        self.signals = []

        self.data['rsi'] = self._calculate_rsi(self.data['close'], self.params["rsi_period"])
        self.data['ma'] = self.data['close'].rolling(window=self.params["ma_period"]).mean()

    def _calculate_rsi(self, series, period):
        delta = series.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    @classmethod
    def generate_param_combinations(cls):
        from itertools import product
        keys = cls.param_grid.keys()
        values = cls.param_grid.values()
        for combo in product(*values):
            yield dict(zip(keys, combo))

    def run(self):
        position = None
        for idx, row in self.data.iterrows():
            if np.isnan(row['rsi']) or np.isnan(row['ma']):
                continue

            ts = pd.to_datetime(row["timestamp"])
            price = row["close"]

            if position is None:
                if row['rsi'] < self.params["rsi_oversold"] and price > row['ma']:
                    self.signals.append({
                        "timestamp": ts,
                        "symbol": self.symbol,
                        "direction": "LONG",
                        "entry_price": price,
                        "take_profit": price * 1.02,
                        "stop_loss": price * 0.98
                    })
                    position = "LONG"
            else:
                if row['rsi'] > self.params["rsi_overbought"] or price < row['ma']:
                    self.signals.append({
                        "timestamp": ts,
                        "symbol": self.symbol,
                        "exit": True,
                        "exit_price": price
                    })
                    position = None

    def get_results(self):
        return self.signals

