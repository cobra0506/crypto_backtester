
import importlib

def load_class_from_string(class_path: str):
    module_path, class_name = class_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    cls = getattr(module, class_name)
    return cls

def calculate_drawdown_and_winrate(trades):
    if not trades:
        return 0.0, 0.0

    balances = [t["balance_after"] for t in trades]
    peak = balances[0]
    max_dd = 0

    for b in balances:
        if b > peak:
            peak = b
        dd = (peak - b) / peak
        max_dd = max(max_dd, dd)

    wins = sum(1 for t in trades if t["net_pnl"] > 0)
    win_rate = (wins / len(trades)) * 100 if trades else 0

    return max_dd * 100, win_rate
