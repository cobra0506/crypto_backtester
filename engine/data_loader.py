# data_loader.py
import pandas as pd
import os

REQUIRED_COLUMNS = ["timestamp", "open", "high", "low", "close", "volume"]

def load_csv(symbol: str, interval: str) -> pd.DataFrame:
    """
    Loads a CSV file for the given symbol and interval into a DataFrame.

    :param symbol: e.g. BTCUSDT
    :param interval: e.g. 1 (for 1m)
    :return: DataFrame with candle data or None if not found/invalid
    """
    filename = f"data/{symbol}_{interval}m.csv"
    if not os.path.exists(filename):
        print(f"❌ File not found: {filename}")
        return None

    try:
        df = pd.read_csv(filename, parse_dates=["timestamp"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        return df
    except Exception as e:
        print(f"❌ Error loading {filename}: {e}")
        return None

def validate_candles(df: pd.DataFrame, interval: int) -> bool:
    """
    Validates the structure and consistency of candle data.

    :param df: Pandas DataFrame
    :param interval: Expected interval in minutes (e.g. 1, 5, 15)
    :return: True if valid, False otherwise
    """
    if df is None or df.empty:
        print("❌ DataFrame is empty or None.")
        return False

    REQUIRED_COLUMNS = ["timestamp", "open", "high", "low", "close", "volume"]
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        print(f"❌ Missing columns: {missing_cols}")
        return False

    # Ensure sorted by timestamp
    if not df["timestamp"].is_monotonic_increasing:
        print("⚠️ Data not sorted by timestamp. Fixing...")
        df.sort_values("timestamp", inplace=True)
        df.reset_index(drop=True, inplace=True)

    # Make sure timestamps are timezone-aware UTC
    if df["timestamp"].dt.tz is None:
        df["timestamp"] = df["timestamp"].dt.tz_localize("UTC")

    # Check for missing timestamps based on the interval
    expected_delta = pd.Timedelta(minutes=interval)
    actual_deltas = df["timestamp"].diff().dropna()

    tolerance = expected_delta * 1.1  # 10% tolerance for slight timing inaccuracies
    gaps = actual_deltas[actual_deltas > tolerance]

    if not gaps.empty:
        print(f"⚠️ Missing candles detected: {len(gaps)} gaps")
        # Optionally, print gap details here
        # for idx in gaps.index:
        #     print(f"Gap between {df['timestamp'].iloc[idx-1]} and {df['timestamp'].iloc[idx]} (diff={actual_deltas.loc[idx]})")

    print("✅ Candle data validated successfully.")
    return True



# ----------- Minimal test -------------
if __name__ == "__main__":
    symbol = "BTCUSDT"
    interval = "1"

    df = load_csv(symbol, interval)
    if df is not None:
        print(f"Loaded {len(df)} candles for {symbol}")
        validate_candles(df)
