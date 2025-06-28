from engine.strategy_interface import BaseStrategy

class ExampleStrategy(BaseStrategy):
    def run(self):
        # Simple placeholder strategy: Buy on every 10th candle, sell 5 candles later
        for i in range(0, len(self.data) - 5, 10):
            entry = self.data.iloc[i]
            exit_ = self.data.iloc[i + 5]

            self.trades.append({
                "symbol": self.symbol,
                "entry_time": entry["timestamp"],
                "entry_price": entry["close"],
                "exit_time": exit_["timestamp"],
                "exit_price": exit_["close"],
                "pnl": exit_["close"] - entry["close"]
            })
