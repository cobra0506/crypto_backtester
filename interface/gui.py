# gui.py

import tkinter as tk
from tkinter import ttk
import threading
import importlib.util
import os
import sys
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import config
from engine.optimizer_gui_runner import run_optimizer_with_params
from engine.trade_engine import discover_strategy_classes

class BacktestGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Backtest GUI")
        self._blink_flag = False

        self.strategy_cb = ttk.Combobox(root, state="readonly")
        self.symbol_cb = ttk.Combobox(root, values=config.SYMBOLS, state="readonly")
        self.interval_cb = ttk.Combobox(root, values=config.INTERVAL, state="readonly")
        self.historical_days_entry = ttk.Entry(root)
        self.historical_days_entry.insert(0, str(config.HISTORICAL_DAYS))

        self.strategy_cb.grid(row=0, column=1)
        self.symbol_cb.grid(row=1, column=1)
        self.interval_cb.grid(row=2, column=1)
        self.historical_days_entry.grid(row=3, column=1)

        ttk.Label(root, text="Strategy:").grid(row=0, column=0)
        ttk.Label(root, text="Symbol:").grid(row=1, column=0)
        ttk.Label(root, text="Interval:").grid(row=2, column=0)
        ttk.Label(root, text="Historical Days:").grid(row=3, column=0)

        self.start_button = ttk.Button(root, text="Start Optimization", command=self.start_optimization)
        self.start_button.grid(row=4, column=0, columnspan=2)

        self.progress_var = tk.StringVar(value="Idle")
        self.status_var = tk.StringVar(value="Ready")

        ttk.Label(root, textvariable=self.progress_var).grid(row=5, column=0, columnspan=2)
        ttk.Label(root, textvariable=self.status_var).grid(row=6, column=0, columnspan=2)

        self.status_light = tk.Label(root, text="●", font=("Arial", 14), fg="gray")
        self.status_light.grid(row=7, column=0, columnspan=2)

        self.canvas_frame = tk.Frame(root)
        self.canvas_frame.grid(row=8, column=0, columnspan=2)
        self.chart_canvas = None

        self.refresh_strategies()

    def refresh_strategies(self):
        strategies = discover_strategy_classes("engine/strategies")
        strategy_paths = [f"{name}.{cls}" for name, cls in strategies]
        self.strategy_cb["values"] = strategy_paths
        if strategy_paths:
            self.strategy_cb.current(0)
        if config.SYMBOLS:
            self.symbol_cb.current(0)
        if config.INTERVAL:
            self.interval_cb.current(0)

    def _blink(self):
        def blink_loop():
            while self._blink_flag:
                self.status_light.config(fg="green")
                self.root.update()
                self.root.after(500)
                self.status_light.config(fg="gray")
                self.root.update()
                self.root.after(500)
        threading.Thread(target=blink_loop, daemon=True).start()

    """def plot_equity_curve(self, equity_curve):
        if self.chart_canvas:
            self.chart_canvas.get_tk_widget().destroy()

        fig, ax = plt.subplots(figsize=(6, 3))
        ax.plot(equity_curve, label="Equity Curve")
        ax.set_title("Test Equity Curve")
        ax.set_xlabel("Trade")
        ax.set_ylabel("Equity")
        ax.legend()

        self.chart_canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
        self.chart_canvas.draw()
        self.chart_canvas.get_tk_widget().pack()"""

    def start_optimization(self):
        strategy_path = self.strategy_cb.get()
        symbol = self.symbol_cb.get()
        interval = self.interval_cb.get()
        try:
            historical_days = int(self.historical_days_entry.get())
        except ValueError:
            self.status_var.set("Invalid historical days.")
            return

        if not strategy_path:
            self.status_var.set("No strategy selected.")
            return

        config.HISTORICAL_DAYS = historical_days  # Override config value

        self.status_var.set("Running Optimization...")
        self._blink_flag = True
        self._blink()
        self.start_button.config(state="disabled")

        def runner():
            try:
                module_name, class_name = strategy_path.split(".")
                spec = importlib.util.spec_from_file_location(module_name, f"engine/strategies/{module_name}.py")
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                StrategyClass = getattr(module, class_name)

                def update_progress(current, total):
                    self.progress_var.set(f"Running {current} of {total}")

                result = run_optimizer_with_params(StrategyClass, update_progress, None)
                if result:
                    top = result[0]
                    self.status_var.set(f"Done! Top test balance: {top['test_final_balance']:.2f}")
                    #if "test_equity_curve" in top:
                        #self.plot_equity_curve(top["test_equity_curve"])
                else:
                    self.status_var.set("No results")
            except Exception as e:
                self.status_var.set(f"Error: {str(e)}")
            finally:
                self._blink_flag = False
                self.status_light.config(fg="gray")
                self.start_button.config(state="normal")

        threading.Thread(target=runner, daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = BacktestGUI(root)
    root.mainloop()



'''import tkinter as tk
from tkinter import ttk
import threading
import importlib.util
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import config
from engine.optimizer_gui_runner import run_optimizer_with_params
from engine.trade_engine import discover_strategy_classes

class BacktestGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Backtest GUI")
        self._blink_flag = False

        self.strategy_cb = ttk.Combobox(root, state="readonly")
        self.symbol_cb = ttk.Combobox(root, values=config.SYMBOLS, state="readonly")
        self.interval_cb = ttk.Combobox(root, values=config.INTERVAL, state="readonly")

        self.strategy_cb.grid(row=0, column=1)
        self.symbol_cb.grid(row=1, column=1)
        self.interval_cb.grid(row=2, column=1)

        ttk.Label(root, text="Strategy:").grid(row=0, column=0)
        ttk.Label(root, text="Symbol:").grid(row=1, column=0)
        ttk.Label(root, text="Interval:").grid(row=2, column=0)

        self.start_button = ttk.Button(root, text="Start Optimization", command=self.start_optimization)
        self.start_button.grid(row=3, column=0, columnspan=2)

        self.progress_var = tk.StringVar(value="Idle")
        self.status_var = tk.StringVar(value="Ready")

        ttk.Label(root, textvariable=self.progress_var).grid(row=4, column=0, columnspan=2)
        ttk.Label(root, textvariable=self.status_var).grid(row=5, column=0, columnspan=2)

        self.status_light = tk.Label(root, text="●", font=("Arial", 14), fg="gray")
        self.status_light.grid(row=6, column=0, columnspan=2)

        self.refresh_strategies()

    def refresh_strategies(self):
        strategies = discover_strategy_classes("engine/strategies")
        strategy_paths = [f"{name}.{cls}" for name, cls in strategies]
        self.strategy_cb["values"] = strategy_paths
        if strategy_paths:
            self.strategy_cb.current(0)
        if config.SYMBOLS:
            self.symbol_cb.current(0)
        if config.INTERVAL:
            self.interval_cb.current(0)

    def _blink(self):
        def blink_loop():
            while self._blink_flag:
                self.status_light.config(fg="green")
                self.root.update()
                self.root.after(500)
                self.status_light.config(fg="gray")
                self.root.update()
                self.root.after(500)
        threading.Thread(target=blink_loop, daemon=True).start()

    def start_optimization(self):
        strategy_path = self.strategy_cb.get()
        symbol = self.symbol_cb.get()
        interval = self.interval_cb.get()

        if not strategy_path:
            self.status_var.set("No strategy selected.")
            return

        self.status_var.set("Running Optimization...")
        self._blink_flag = True
        self._blink()
        self.start_button.config(state="disabled")

        def runner():
            try:
                module_name, class_name = strategy_path.split(".")
                spec = importlib.util.spec_from_file_location(module_name, f"engine/strategies/{module_name}.py")
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                StrategyClass = getattr(module, class_name)

                def update_progress(current, total):
                    self.progress_var.set(f"Running {current} of {total}")

                result = run_optimizer_with_params(StrategyClass, symbol, interval, update_progress)
                if result:
                    self.status_var.set(f"Done! Top test balance: {result[0]['test_final_balance']:.2f}")
                else:
                    self.status_var.set("No results")
            except Exception as e:
                self.status_var.set(f"Error: {str(e)}")
            finally:
                self._blink_flag = False
                self.status_light.config(fg="gray")
                self.start_button.config(state="normal")

        threading.Thread(target=runner, daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = BacktestGUI(root)
    root.mainloop()
'''