import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from engine.data_loader import load_csv, validate_candles
from engine.strategies.example_strategy import ExampleStrategy  # swap here for different strategy

class PortfolioManager:
    def __init__(self, starting_balance: float, fee_pct: float = 0.001, slippage_pct: float = 0.0005):
        self.balance = starting_balance
        self.fee_pct = fee_pct
        self.slippage_pct = slippage_pct
        self.trade_log = []

    def process_trade(self, trade):
        # Calculate fees and slippage on entry and exit
        entry_price = trade["entry_price"] * (1 + self.slippage_pct)
        exit_price = trade["exit_price"] * (1 - self.slippage_pct)

        trade_size = 1  # For simplicity assume 1 unit size; extend later
        gross_pnl = (exit_price - entry_price) * trade_size

        fee = (entry_price + exit_price) * trade_size * self.fee_pct
        net_pnl = gross_pnl - fee

        self.balance += net_pnl

        # Record trade with net PnL and fees
        trade_record = trade.copy()
        trade_record.update({
            "net_pnl": net_pnl,
            "fee": fee,
            "balance_after": self.balance
        })
        self.trade_log.append(trade_record)

    def summary(self):
        return {
            "final_balance": self.balance,
            "total_trades": len(self.trade_log)
        }

def run_strategy_for_symbol(symbol: str, interval: str, config: dict):
    df = load_csv(symbol, interval)
    if not validate_candles(df):
        print(f"❌ Invalid data for {symbol}, skipping.")
        return []

    strategy = ExampleStrategy(symbol, interval, df, config)
    strategy.run()
    return strategy.get_results()

if __name__ == "__main__":
    symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]  # Add as many as you want here
    interval = "1"
    config = {}  # Strategy params

    portfolio = PortfolioManager(starting_balance=10000)

    for symbol in symbols:
        print(f"▶ Running strategy for {symbol}")
        trades = run_strategy_for_symbol(symbol, interval, config)
        print(f"→ {len(trades)} trades from {symbol}")

        for trade in trades:
            portfolio.process_trade(trade)

    summary = portfolio.summary()
    print(f"\n🧾 Portfolio summary:")
    print(f"Starting balance: 10000")
    print(f"Final balance: {summary['final_balance']:.2f}")
    print(f"Total trades: {summary['total_trades']}")
