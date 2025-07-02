# export_utils.py
import csv
import json
from typing import List, Dict

'''def export_trades_to_csv(trades: List[Dict], filename: str) -> None:
    if not trades:
        print("No trades to export.")
        return
    keys = trades[0].keys()
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(trades)
    print(f"Trades exported to {filename}")'''

'''def export_summary_to_csv(summary: Dict, filename: str) -> None:
    if not summary:
        print("No summary to export.")
        return
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=summary.keys())
        writer.writeheader()
        writer.writerow(summary)
    print(f"Summary exported to {filename}")'''

def export_optimizer_top_configs(results: List[Dict], filename: str, top_n: int = 10) -> None:
    if not results:
        print("No optimization results to export.")
        return
    sorted_results = sorted(results, key=lambda x: x.get("test_final_balance", 0), reverse=True)
    top_results = sorted_results[:top_n]
    keys = ["test_id"] + [k for k in top_results[0].keys() if k != "test_id"]
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(top_results)
    print(f"Top {top_n} configs exported to {filename}")

'''def export_to_json(data: List[Dict], filename: str) -> None:
    if not data:
        print("No data to export.")
        return
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    print(f"Data exported to {filename}")'''

def save_results(results: List[Dict], filename: str = "optimizer_results.csv") -> None:
    if not results:
        print("No results to save.")
        return
    keys = ["test_id"] + [k for k in results[0].keys() if k != "test_id"]
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(results)
    print(f"All optimization results saved to {filename}")
