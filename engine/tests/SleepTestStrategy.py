from engine.strategies.base_strategy import BaseStrategy

class SleepTestStrategy(BaseStrategy):
    param_grid = {
        "entry_interval": [1, 3, 5],
        "exit_offset": [5, 10],
    }

    def run(self):
        self.signals = []
        df = self.df

        for i in range(1, len(df)):
            if i % self.params["entry_interval"] == 0:
                entry_price = df.iloc[i]["close"]
                exit_index = min(i + self.params["exit_offset"], len(df) - 1)
                exit_price = df.iloc[exit_index]["close"]
                pnl = exit_price - entry_price

                self.signals.append({
                    "timestamp": df.iloc[exit_index]["timestamp"],
                    "symbol": self.symbol,
                    "price": exit_price,
                    "action": "exit",
                    "net_pnl": pnl,
                    "entry_price": entry_price
                })

    def get_results(self):
        return self.signals
