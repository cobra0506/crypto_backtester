import pandas as pd

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
        self.starting_balance = starting_balance

    def process_signal(self, signal):
        symbol = signal.get("symbol")
        timestamp = signal.get("timestamp")
        action = signal.get("action")
        price = signal.get("price") or signal.get("entry_price")

        if action is None:
            raise ValueError("Signal must include 'action' key")

        # Handle price update action
        if action == "price_update":
            if symbol is None or price is None:
                # Missing required info, ignore
                return
            pos = self.positions.get(symbol)
            if pos is None:
                # No open position to update
                return

            # Check if position should exit
            should_exit, exit_price = pos.should_exit(price)
            if should_exit:
                self._close_position(symbol, timestamp, exit_price)
            return

        # Handle closing positions manually
        if action == "close_long":
            if symbol in self.positions and self.positions[symbol].direction == "LONG":
                self._close_position(symbol, timestamp, price)
            return
        elif action == "close_short":
            if symbol in self.positions and self.positions[symbol].direction == "SHORT":
                self._close_position(symbol, timestamp, price)
            return

        # Handle opening positions
        if action == "open_long":
            if symbol in self.positions:
                return  # Already in position, ignore
            direction = "LONG"
        elif action == "open_short":
            if symbol in self.positions:
                return
            direction = "SHORT"
        else:
            raise ValueError(f"Unknown action: {action}")

        if price is None:
            raise ValueError("Open position signal must include price")

        # Position sizing
        risk_amount = self.balance * self.risk_per_trade
        qty = risk_amount / price

        pos = Position(
            symbol=symbol,
            direction=direction,
            entry_time=timestamp,
            entry_price=price,
            qty=qty,
            tp=signal.get("tp") or signal.get("take_profit"),
            sl=signal.get("sl") or signal.get("stop_loss"),
            trailing=signal.get("trailing")
        )
        self.positions[symbol] = pos



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

    def get_summary(self):
        return {
            "final_balance": self.balance,
            "total_trades": len(self.trades)
        }
