# ✅ Crypto Backtester Development Plan

This file tracks development stages and tests. Each stage builds on the last. Only proceed if all tests pass.

---

## 🔧 Setup

- [x] Create `crypto_backtester/` project
- [x] Add folder structure and placeholder files

---

## 🧩 Stage 1 – Fetch Candle Data

- [x] `data_handler.fetch_data(symbol, timeframe, start, end)`
- [x] Save CSV to `/data/SYMBOL_TIMEFRAME.csv`
- [x] Log download time, row count

✅ **Test**:
- [x] Download BTCUSDT 1h from 2024-01-01 to 2024-01-10
- [x] CSV file is saved and contains correct range

---

## 🧩 Stage 2 – Validate Local Data

- [x] `data_handler.is_data_valid(...)`
- [x] Detect missing/incomplete/corrupt files

✅ **Test**:
- [x] Rename CSV → triggers re-download
- [x] Truncated file → triggers re-download

---

## 🧩 Stage 3 – Load Data to Backtrader

- [ ] Load CSV to Backtrader via `bt.feeds.PandasData`
- [ ] Support timezones if needed

✅ **Test**:
- [ ] Print first/last timestamp from feed
- [ ] Check for gaps or NaNs

---

## 🧩 Stage 4 – Strategy Plug-In System

- [ ] Store strategy name in `config.py`
- [ ] Load strategy class via `importlib`

✅ **Test**:
- [ ] Switch between 2 test strategies
- [ ] Confirm no code change needed outside config

---

## 🧩 Stage 5 – Run Strategy on 1 Symbol

- [ ] Load feed
- [ ] Run strategy on symbol+timeframe

✅ **Test**:
- [ ] Output final balance
- [ ] Confirm trades triggered correctly

---

## 🧩 Stage 6 – Multi-Symbol, Shared Portfolio

- [ ] Load 2+ symbols into one Cerebro instance
- [ ] Share a single cash balance

✅ **Test**:
- [ ] Confirm total portfolio performance
- [ ] Log trade count and PnL per symbol

---

## 🧩 Stage 7 – Slippage & Commissions

- [ ] Add slippage model (`set_slippage_perc`)
- [ ] Add broker commissions

✅ **Test**:
- [ ] Run strategy w/ and w/o slippage
- [ ] Compare final balances

---

## 🧩 Stage 8 – Analyzer Stats

- [ ] Add Sharpe, Win Rate, Drawdown, PnL Curve

✅ **Test**:
- [ ] Print stats at end
- [ ] Save to CSV file

---

## 🧩 Stage 9 – Batch Tests + Result Logging

- [ ] Run loop across strategies/symbols/timeframes/params
- [ ] Save each run to `all_tests.csv`
- [ ] Track Top N results to `top_10.csv`

✅ **Test**:
- [ ] CSV files saved
- [ ] Top 10 matches final balances

---

## 🧩 Stage 10 – Walk-Forward Optimization

- [ ] Divide data into training/validation slices
- [ ] Optimize on train, test on validate

✅ **Test**:
- [ ] Log best param per segment
- [ ] Show validation vs train difference

---

## 🧩 Stage 11 – Regression Testing

- [ ] `regression_tester.compare_expected(result)`
- [ ] Save expected results hash

✅ **Test**:
- [ ] Compare result hash after refactor
- [ ] Flag mismatch if logic breaks

---

## 🧩 Stage 12 – GUI (Optional)

- [ ] Build simple Tkinter UI
- [ ] Progress bar, log window, start/stop buttons

✅ **Test**:
- [ ] GUI remains responsive
- [ ] Show current stage or log message

---

## 🧩 Stage 13 – Extra Features

- [ ] Plot equity curves
- [ ] Telegram alerts
- [ ] Symbol auto-filtering


crypto_backtester/
│
├── main.py                    # Entrypoint, runs the system
├── config.py                  # Global user config (symbols, timeframes, etc.)
├── requirements.txt           # All Python deps
├── README.md                  # Basic usage guide
├── PROJECT_PLAN.md            # Full stage plan with checkboxes ✅
│
├── /data/                     # Candle CSVs
│   └── BTCUSDT_1h.csv
│
├── /results/                  # Logs, CSVs, equity curves
│   ├── all_tests.csv
│   ├── top_10.csv
│   └── equity_BTCUSDT.png
│
├── /strategies/              # Your plug-in strategy classes
│   ├── __init__.py
│   ├── sample_strategy.py
│   └── breakout_strategy.py
│
├── /engine/                   # Core modules (engine logic)
│   ├── data_handler.py        # Fetch/validate/load OHLCV
│   ├── strategy_runner.py     # Wraps Backtrader execution
│   ├── optimizer.py           # Walk-forward, grid/random search
│   ├── analyzers.py           # Sharpe, DD, trade logs, etc.
│   ├── regression_tester.py   # Validates result integrity after code changes
│   └── utils.py               # Shared helpers
│
├── /gui/                      # Optional GUI layer (Tkinter)
│   └── gui_app.py
