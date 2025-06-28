# config.py

SYMBOLS = ["BTCUSDT",  "ETHUSDT",  "BNBUSDT",  "ADAUSDT",  "SOLUSDT",  "DOTUSDT",  "DOGEUSDT"]
INTERVAL = ["1", "5", "15", "30", "60", "240"]  # 1-minute interval

START_BALANCE = 10000.0

# Bybit download config
HISTORICAL_DAYS = 30  # How many days to fetch if missing/incomplete

# Fees and slippage
FEE_PCT = 0.001  # 0.1%
SLIPPAGE_PCT = 0.0005  # 0.05%
