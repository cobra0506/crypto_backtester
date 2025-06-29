import os
import csv
import pytest
import sys
import os


# Add the 'engine' folder (parent of 'tests') to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from export_utils import export_optimizer_top_configs

def test_export_optimizer_top_configs_creates_file_and_content(tmp_path):
    sample_results = [
        {"param1": 1, "param2": 5, "test_final_balance": 100.0},
        {"param1": 2, "param2": 3, "test_final_balance": 200.0},
        {"param1": 3, "param2": 7, "test_final_balance": 150.0},
    ]

    filename = tmp_path / "top_configs.csv"

    export_optimizer_top_configs(sample_results, str(filename), top_n=2)

    # Check file exists
    assert filename.exists()

    # Check CSV content
    with open(filename, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 2
        # Should be sorted descending by test_final_balance
        assert rows[0]["param1"] == "2"  # highest balance
        assert rows[1]["param1"] == "3"

if __name__ == "__main__":
    pytest.main()
