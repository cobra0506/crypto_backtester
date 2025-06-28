import requests
import pandas as pd
import os
import time
from datetime import datetime, timedelta, timezone

BYBIT_ENDPOINT = "https://api.bybit.com/v5/market/kline"

def interval_to_timedelta(interval: str) -> timedelta:
    # Only supports minute intervals for now
    return timedelta(minutes=int(interval))

def fetch_bybit_candles(symbol: str, interval: str, start: datetime, end: datetime, max_retries=5) -> pd.DataFrame:
    if start.tzinfo is None or end.tzinfo is None:
        raise ValueError("Start and end must be timezone-aware (UTC).")

    category = "linear"
    start_ms = int(start.timestamp() * 1000)
    end_ms = int(end.timestamp() * 1000)
    limit = 1000  # max candles per request

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
            print(f"⚠️ Error fetching {symbol} {interval}m: {e} (attempt {attempt + 1}/{max_retries})")
            time.sleep(1)

    print(f"❌ Failed fetching {symbol} {interval}m candles after retries.")
    return pd.DataFrame()

def fetch_and_save_candles(symbol: str, interval: str, days: int) -> bool:
    try:
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=days)

        all_dfs = []
        fetch_start = start_time

        while fetch_start < end_time:
            chunk = interval_to_timedelta(interval) * 999
            fetch_end = fetch_start + chunk
            if fetch_end > end_time:
                fetch_end = end_time

            df = fetch_bybit_candles(symbol, interval, fetch_start, fetch_end)
            if df.empty:
                print(f"❌ No data for {symbol} {interval}m from {fetch_start} to {fetch_end}")
                break

            all_dfs.append(df)

            last_ts = df["timestamp"].iloc[-1]
            if last_ts.tzinfo is None:
                last_ts = last_ts.replace(tzinfo=timezone.utc)

            fetch_start = last_ts + interval_to_timedelta(interval)

        if not all_dfs:
            return False

        full_df = pd.concat(all_dfs).drop_duplicates("timestamp").reset_index(drop=True)
        save_candles_to_csv(full_df, symbol, interval)
        return True

    except Exception as e:
        print(f"❌ Exception in fetch_and_save_candles: {e}")
        return False

def save_candles_to_csv(df: pd.DataFrame, symbol: str, interval: str):
    os.makedirs("data", exist_ok=True)
    filename = f"data/{symbol}_{interval}m.csv"
    df.to_csv(filename, index=False)
    print(f"✅ Saved {len(df)} rows to {filename}")

if __name__ == "__main__":
    SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    INTERVALS = ["1", "5", "15", "30", "60", "240"]
    HISTORICAL_DAYS = 30

    for symbol in SYMBOLS:
        for interval in INTERVALS:
            print(f"⬇️ Downloading {symbol} {interval}m candles for {HISTORICAL_DAYS} days...")
            success = fetch_and_save_candles(symbol, interval, HISTORICAL_DAYS)
            if success:
                print(f"✅ Finished {symbol} {interval}m")
            else:
                print(f"❌ Failed {symbol} {interval}m")
