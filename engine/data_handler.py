import requests
import pandas as pd
import os
import time
import asyncio
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

def fetch_and_save_candles(symbol: str, interval: str, days: int) -> bool:
    """Fetch 'days' days of candles for symbol/interval and save CSV.

    Calls fetch_bybit_candles repeatedly if needed to cover full range.
    """
    try:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)

        all_dfs = []
        fetch_start = start_time

        while fetch_start < end_time:
            fetch_end = fetch_start + timedelta(minutes=1000 * int(interval))  # 1000 candles max per request
            if fetch_end > end_time:
                fetch_end = end_time

            df = fetch_bybit_candles(symbol, interval, fetch_start, fetch_end)
            if df.empty:
                print(f"❌ No data returned for {symbol} {interval}m from {fetch_start} to {fetch_end}")
                break

            all_dfs.append(df)
            last_timestamp = df["timestamp"].iloc[-1]
            fetch_start = last_timestamp + timedelta(minutes=int(interval))  # next batch start

            # Safety break in case timestamps don’t advance
            if fetch_start <= last_timestamp:
                break

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
