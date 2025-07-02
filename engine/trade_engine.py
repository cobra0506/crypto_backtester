# trade_engine.py
import pandas as pd
import os
import importlib.util
from config import POSITION_MODE, FIXED_TRADE_AMOUNT, RISK_PCT

class Position:
    def __init__(self, symbol, direction, entry_time, entry_price, qty, tp=None, sl=None, trailing=None):
        self.symbol = symbol
        self.direction = direction
        self.entry_time = entry_time
        self.entry_price = entry_price
        self.qty = qty
        self.tp = tp
        self.sl = sl
        self.trailing = trailing or {}
        self.trailing_active = False
        self.exit_time = None
        self.exit_price = None

    def update_trailing_tp(self, price):
        if self.direction == "LONG":
            if not self.trailing_active:
                self.tp = price * (1 + self.trailing["pct"])
                self.trailing_active = True
            elif price > self.entry_price:
                new_tp = price * (1 + self.trailing["pct"])
                if new_tp > self.tp:
                    self.tp = new_tp
        elif self.direction == "SHORT":
            if not self.trailing_active:
                self.tp = price * (1 - self.trailing["pct"])
                self.trailing_active = True
            elif price < self.entry_price:
                new_tp = price * (1 - self.trailing["pct"])
                if new_tp < self.tp:
                    self.tp = new_tp

    def should_exit(self, price):
        if self.trailing:
            self.update_trailing_tp(price)
        if self.direction == "LONG":
            if self.tp and price >= self.tp:
                return True, self.tp
            if self.sl and price <= self.sl:
                return True, self.sl
        else:
            if self.tp and price <= self.tp:
                return True, self.tp
            if self.sl and price >= self.sl:
                return True, self.sl
        return False, None


class TradeEngine:
    def __init__(self, starting_balance=10000, fee_pct=0.001, slippage_pct=0.001, risk_per_trade=0.01):
        self.positions = {}
        self.trades = []
        self.fee_pct = fee_pct
        self.slippage_pct = slippage_pct
        self.risk_per_trade = risk_per_trade
        self.balance = starting_balance
        self.available_balance = starting_balance
        self.starting_balance = starting_balance

        # Equity tracking for max drawdown
        self.max_equity = starting_balance
        self.max_drawdown = 0.0
        self.equity_curve = []  # list of dicts with timestamp and balance

    def process_signal(self, signal):
        timestamp = signal["timestamp"]
        symbol = signal["symbol"]

        # Handle price update signals (no trade open/close)
        if signal.get("action") == "price_update":
            price = signal["price"]
            if symbol in self.positions:
                pos = self.positions[symbol]
                exit_flag, exit_price = pos.should_exit(price)
                if exit_flag:
                    self._close_position(symbol, timestamp, exit_price)
            self._track_equity(timestamp)
            return

        price = signal.get("price") or signal.get("entry_price") or signal.get("exit_price")
        if price is None:
            raise ValueError("Signal must include 'price', 'entry_price' or 'exit_price'")

        # Close position on exit signal
        if signal.get("exit", False):
            if symbol in self.positions:
                self._close_position(symbol, timestamp, price)
            self._track_equity(timestamp)
            return

        # Check if existing position needs closing by TP/SL
        if symbol in self.positions:
            pos = self.positions[symbol]
            exit_flag, exit_price = pos.should_exit(price)
            if exit_flag:
                self._close_position(symbol, timestamp, exit_price)
            self._track_equity(timestamp)
            return

        # Opening new position
        direction = signal["direction"]
        entry_price = signal.get("entry_price", price)

        if POSITION_MODE == "fixed":
            amount_to_use = FIXED_TRADE_AMOUNT
        else:
            amount_to_use = self.available_balance * RISK_PCT

        if amount_to_use > self.available_balance:
            print(f"❌ Not enough available balance to open position for {symbol}. Skipping.")
            self._track_equity(timestamp)
            return

        qty = amount_to_use / entry_price

        pos = Position(
            symbol=symbol,
            direction=direction,
            entry_time=timestamp,
            entry_price=entry_price,
            qty=qty,
            tp=signal.get("take_profit"),
            sl=signal.get("stop_loss"),
            trailing=signal.get("trailing")
        )

        self.positions[symbol] = pos
        self.available_balance -= amount_to_use

        self._track_equity(timestamp)

    def _close_position(self, symbol, exit_time, exit_price):
        pos = self.positions[symbol]
        direction = pos.direction
        entry_price = pos.entry_price
        qty = pos.qty

        if direction == "LONG":
            gross = (exit_price - entry_price) * qty
        else:
            gross = (entry_price - exit_price) * qty

        fee = (entry_price + exit_price) * qty * self.fee_pct
        slip = (entry_price + exit_price) * qty * self.slippage_pct
        net = gross - fee - slip

        self.balance += net
        self.available_balance += (entry_price * qty) + net  # initial capital + PnL

        self.trades.append({
            "symbol": symbol,
            "direction": direction,
            "entry_time": pos.entry_time,
            "exit_time": exit_time,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "qty": qty,
            "gross_pnl": gross,
            "fee": fee,
            "slippage": slip,
            "net_pnl": net,
            "balance_after": self.balance
        })
        del self.positions[symbol]

    def close_all(self, final_time, final_price):
        for symbol in list(self.positions.keys()):
            self._close_position(symbol, final_time, final_price)

    def get_trades(self):
        return self.trades

    def _track_equity(self, timestamp):
        current_equity = self.balance
        self.equity_curve.append({"timestamp": timestamp, "balance": current_equity})

        if current_equity > self.max_equity:
            self.max_equity = current_equity
        else:
            drawdown = self.max_equity - current_equity
            drawdown_pct = drawdown / self.max_equity
            if drawdown_pct > self.max_drawdown:
                self.max_drawdown = drawdown_pct

    def get_summary(self):
        # Save equity curve to CSV
        df = pd.DataFrame(self.equity_curve)
        df.to_csv("equity_curve.csv", index=False)

        return {
            "final_balance": self.balance,
            "total_trades": len(self.trades),
            "max_drawdown_pct": self.max_drawdown * 100,
        }


def discover_strategy_classes(directory):
    strategy_classes = []
    for filename in os.listdir(directory):
        if filename.endswith(".py") and not filename.startswith("__"):
            module_name = filename[:-3]
            filepath = os.path.join(directory, filename)
            spec = importlib.util.spec_from_file_location(module_name, filepath)
            module = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(module)
                for attr_name in dir(module):
                    obj = getattr(module, attr_name)
                    if isinstance(obj, type) and hasattr(obj, "generate_param_combinations"):
                        strategy_classes.append((module_name, attr_name))
            except Exception as e:
                print(f"Error loading {filename}: {e}")
    return strategy_classes
