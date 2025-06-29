from engine.data_loader import load_csv, validate_candles
from engine.data_handler import fetch_and_save_candles
import config
import os

def test_download_and_validation():
    print("🔧 Testing data download and validation...\n")
    for symbol in config.SYMBOLS:
        for interval in config.INTERVAL:
            print(f"→ Checking {symbol} {interval}m...")
            fetch_and_save_candles(symbol, interval, config.HISTORICAL_DAYS)

            df = load_csv(symbol, interval)
            assert df is not None and not df.empty, f"{symbol} {interval}m failed to load"
            assert validate_candles(df, int(interval)), f"{symbol} {interval}m failed validation"
    print("\n✅ All symbols and intervals passed download + validation.")

def test_files_exist():
    print("\n🗂 Verifying files exist...")
    for symbol in config.SYMBOLS:
        for interval in config.INTERVAL:
            file = f"data/{symbol}_{interval}m.csv"
            assert os.path.isfile(file), f"{file} does not exist!"
    print("✅ All expected files found.")

if __name__ == "__main__":
    test_download_and_validation()
    test_files_exist()
