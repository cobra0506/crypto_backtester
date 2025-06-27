import requests
import pandas as pd
import os
import time
from datetime import datetime, timedelta

BYBIT_ENDPOINT = "https://api.bybit.com/v5/market/kline"

def fetch_bybit_candles(symbol: str, interval: str, start: datetime, end: datetime, max_retries=5) -> pd.DataFrame:
    """
    Fetch historical candles from Bybit v5 API.

    :param symbol: e.g. "BTCUSDT"
    :param interval: e.g. "1", "5", "15", "60", "240", "D"
    :param start: datetime UTC
    :param end: datetime UTC
    :param max_retries: retry attempts per request
    :return: DataFrame with timestamp, open, high, low, close, volume
    """
    all_candles = []
    category = "linear"
    start_ms = int(start.timestamp() * 1000)
    end_ms = int(end.timestamp() * 1000)
    limit = 1000  # max allowed

    for attempt in range(max_retries):
        try:
            params = {
                "category": category,
                "symbol": symbol,
                "interval": interval,
                "start": start_ms,
                "end": end_ms,
                "limit": limit
            }
            response = requests.get(BYBIT_ENDPOINT, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data["retCode"] != 0:
                raise Exception(f"Bybit API error: {data.get('retMsg')}")

            candles = data["result"]["list"]
            if not candles:
                return pd.DataFrame()

            parsed = [{
                "timestamp": int(c[0]) // 1000,
                "open": float(c[1]),
                "high": float(c[2]),
                "low": float(c[3]),
                "close": float(c[4]),
                "volume": float(c[5])
            } for c in candles]

            df = pd.DataFrame(parsed)
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s", utc=True)
            return df.sort_values("timestamp").reset_index(drop=True)

        except Exception as e:
            print(f"⚠️ Error fetching: {e} (attempt {attempt + 1}/{max_retries})")
            time.sleep(1)

    print("❌ Failed to fetch candles after retries.")
    return pd.DataFrame()

def save_candles_to_csv(df: pd.DataFrame, symbol: str, interval: str):
    os.makedirs("data", exist_ok=True)
    filename = f"data/{symbol}_{interval}m.csv"
    df.to_csv(filename, index=False)
    print(f"✅ Saved {len(df)} rows to {filename}")

# ---------- Test Run ----------
if __name__ == "__main__":
    symbol = "BTCUSDT"
    interval = "1"  # 1-minute
    start = datetime.utcnow() - timedelta(days=1)
    end = datetime.utcnow()

    print(f"🔍 Fetching {symbol} {interval}m candles from {start} to {end}")
    df = fetch_bybit_candles(symbol, interval, start, end)

    if df.empty:
        print("❌ No data fetched.")
    else:
        print(f"✅ Fetched {len(df)} candles.")
        save_candles_to_csv(df, symbol, interval)
