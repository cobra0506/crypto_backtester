# config.py

#SYMBOLS = ["BTCUSDT",  "ETHUSDT",  "BNBUSDT",  "ADAUSDT",  "SOLUSDT",  "DOTUSDT",  "DOGEUSDT"]
SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT"]
#INTERVAL = ["1"]#, "5", "15", "30", "60", "240"]  # 1-minute interval
INTERVAL = ["1", "5", "15"]

START_BALANCE = 10000.0

# Bybit download config
HISTORICAL_DAYS = 90  # How many days to fetch if missing/incomplete

# Example: 'engine.strategies.example_strategy.ExampleStrategy'
STRATEGY_CLASS = "engine.strategies.moving_average_cross_strategy.MovingAverageCrossStrategy"

# Fees and slippage
FEE_PCT = 0.001  # 0.1%
SLIPPAGE_PCT = 0.001  # 0.05%

# position size
POSITION_MODE = "fixed"  # "fixed" or "percent"
FIXED_TRADE_AMOUNT = 10  # Used if POSITION_MODE is "fixed"
RISK_PCT = 0.01          # Used if POSITION_MODE is "percent" percent of available balance
