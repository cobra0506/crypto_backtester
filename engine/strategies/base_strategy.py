# strategies/base_strategy.py
class BaseStrategy:
    def __init__(self, df, account, symbol):
        self.df = df
        self.account = account
        self.symbol = symbol
        self.trades = []

    def run(self):
        for i in range(1, len(self.df)):
            row = self.df.iloc[i]
            price = row['close']

            if i % 10 == 0:  # Dummy entry every 10 candles
                success = self.account.enter_trade(self.symbol, price, size=1)
                if success:
                    self.trades.append({'entry': price, 'type': 'buy', 'timestamp': row['timestamp']})
            elif i % 10 == 5 and self.symbol in self.account.positions:
                pnl = self.account.exit_trade(self.symbol, price)
                self.trades.append({'exit': price, 'pnl': pnl, 'timestamp': row['timestamp']})

    def get_results(self):
        return self.trades
