# 🧠 Project Plan – Crypto Backtester

---

## ✅ Stage 1 – Download Historical Data
- [x] Fetch 1m OHLCV candles via Bybit v5 API
- [x] Save per symbol/interval as CSV
- [x] Automatic re-download if file missing/incomplete

✅ **Test**
- [x] Run standalone: `data_handler.py`  
- [x] Data appears under `/data/`
- [x] Re-run detects file exists and skips/fixes

---

## ✅ Stage 2 – Validate Local Data
- [x] Load CSV using Pandas
- [x] Check required columns + sort timestamps
- [x] Detect gaps (based on interval)
- [x] Return cleaned DataFrame

✅ **Test**
- [x] Run `data_loader.py`
- [x] Print number of candles and any validation warnings

---

## ✅ Stage 3.1 – Strategy Interface + Runner
- [x] Create `BaseStrategy` class with `run()` and `get_results()`
- [x] Example strategy runs on 1 symbol
- [x] Results are printed (entry, exit, pnl)

✅ **Test**
- [x] Run `strategy_runner.py`
- [x] Strategy executes and logs mock trades

---

## ⏳ Stage 3.2 – Multi-Symbol Execution + Balance Logic
- [ ] Run strategy across multiple symbols (same timeframe)
- [ ] Use shared balance across all symbols
- [ ] Each trade adjusts account balance
- [ ] Slippage + fees applied to each trade

✅ **Test**
- [ ] Run across 2–3 symbols
- [ ] Print trades and final balance

---

## ⏳ Stage 4 – Trade Engine + Realism Layer
- [ ] Add trade execution logic with:
    - [ ] Entry/exit logic
    - [ ] TP/SL
    - [ ] Order size from risk %
    - [ ] Fees/slippage config
- [ ] Track equity, drawdown, position sizes

✅ **Test**
- [ ] Validate final balance, total trades, drawdown from test logs

---

## ⏳ Stage 5 – Strategy Optimization (Walk-Forward)
- [ ] Define param grid per strategy
- [ ] Run WFA loop:
    - Train segment → optimize
    - Test segment → validate
- [ ] Avoid parameter overfit

✅ **Test**
- [ ] Save top 10 configs per run
- [ ] Save full test history per param set

---

## ⏳ Stage 6 – Exporting Results
- [ ] Save:
    - [ ] All trades to CSV
    - [ ] Summary file with metrics per run
    - [ ] Top-N file with best configs
- [ ] Optional JSON for import into other tools

✅ **Test**
- [ ] Open results in Excel and inspect summary

---

## ⏳ Stage 7 – GUI (Optional, Later)
- [ ] Basic Tkinter GUI
- [ ] Select strategy, symbols, timeframe, dates
- [ ] Show “Running…” progress and current stage

---

## ⏳ Stage X – (Optional) Backtrader Integration
- [ ] Use `bt.feeds.PandasData`
- [ ] Validate strategy results in trusted engine
- [ ] Compare PnL / trades with custom engine
