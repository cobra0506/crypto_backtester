import sys
from pathlib import Path
import pandas as pd

# Fix: Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent))
from config import SYMBOLS, INTERVAL

def check_gaps(filename, expected_interval_minutes):
    print(f"\nChecking gaps in {filename} (expected interval: {expected_interval_minutes}m)")
    try:
        df = pd.read_csv(filename, parse_dates=["timestamp"])
        df = df.sort_values("timestamp").reset_index(drop=True)
        
        expected_delta = pd.Timedelta(minutes=expected_interval_minutes)
        deltas = df["timestamp"].diff().dropna()

        gaps = deltas[deltas > expected_delta * 1.1]  # 10% tolerance
        
        if gaps.empty:
            print("✅ No gaps found.")
        else:
            print(f"⚠️ Found {len(gaps)} gaps:")
            for idx, delta in gaps.items():
                gap_start = df.loc[idx - 1, "timestamp"]
                gap_end = df.loc[idx, "timestamp"]
                gap_minutes = delta / pd.Timedelta(minutes=1)
                print(f"  Gap {idx}: {gap_start} -> {gap_end} = {gap_minutes:.2f} minutes")
        return len(gaps)
    
    except FileNotFoundError:
        print(f"❌ File not found: {filename}")
        return 0
    except Exception as e:
        print(f"❌ Failed to check {filename}: {str(e)}")
        return 0

if __name__ == "__main__":
    total_gaps = 0
    missing_files = 0
    
    for symbol in SYMBOLS:
        for interval in INTERVAL:
            filename = f"data/{symbol}_{interval}m.csv"
            gaps_found = check_gaps(filename, expected_interval_minutes=int(interval))
            total_gaps += gaps_found
            if gaps_found == 0 and not Path(filename).exists():
                missing_files += 1
    
    print("\n=== Summary ===")
    print(f"Total symbols checked: {len(SYMBOLS)}")
    print(f"Total intervals checked per symbol: {len(INTERVAL)}")
    print(f"Total files missing: {missing_files}")
    print(f"Total gaps found: {total_gaps}")