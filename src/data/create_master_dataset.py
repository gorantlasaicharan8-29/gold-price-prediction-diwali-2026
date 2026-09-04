"""Create the IBJA-left master dataset with supporting market features."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
IBJA_PATH = PROJECT_ROOT / "data" / "raw" / "ibja_gold_999_2025_2026.csv"
MARKET_PATH = PROJECT_ROOT / "data" / "raw" / "international_market_data.csv"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "gold_master_dataset.csv"
REPORT_PATH = PROJECT_ROOT / "reports" / "master_dataset_validation.txt"


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load both source files and normalize only their merge-key dates."""
    ibja = pd.read_csv(IBJA_PATH)
    market = pd.read_csv(MARKET_PATH)
    ibja["date"] = pd.to_datetime(ibja["date"], errors="raise")
    market["date"] = pd.to_datetime(market["date"], errors="raise")
    return ibja, market


def validate_master(master: pd.DataFrame) -> dict[str, object]:
    """Collect validation values without filling or changing missing observations."""
    market_columns = [
        "gold_usd_close",
        "gold_usd_open",
        "gold_usd_high",
        "gold_usd_low",
        "usdinr_close",
        "usdinr_open",
        "usdinr_high",
        "usdinr_low",
    ]
    return {
        "rows": len(master),
        "earliest_date": master["date"].min().strftime("%Y-%m-%d"),
        "latest_date": master["date"].max().strftime("%Y-%m-%d"),
        "duplicate_dates": int(master["date"].duplicated().sum()),
        "missing_target": int(master["target_gold_999"].isna().sum()),
        "minimum_target": master["target_gold_999"].min(),
        "maximum_target": master["target_gold_999"].max(),
        "missing_market": {column: int(master[column].isna().sum()) for column in market_columns},
        "market_rows_present": int(master[market_columns].notna().any(axis=1).sum()),
        "missing_values": {column: int(master[column].isna().sum()) for column in master.columns},
    }


def format_report(validation: dict[str, object], master: pd.DataFrame, original_ibja_rows: int) -> str:
    """Format the validation report for reproducible review."""
    missing_market = validation["missing_market"]
    market_percentage = validation["market_rows_present"] / len(master) * 100 if len(master) else 0
    return "\n".join(
        [
            "MASTER DATASET VALIDATION",
            "",
            f"Rows: {validation['rows']}",
            f"Earliest date: {validation['earliest_date']}",
            f"Latest date: {validation['latest_date']}",
            f"Duplicate dates: {validation['duplicate_dates']}",
            "",
            "IBJA TARGET",
            f"Missing target values: {validation['missing_target']}",
            f"Minimum target: {validation['minimum_target']}",
            f"Maximum target: {validation['maximum_target']}",
            "",
            "INTERNATIONAL GOLD FEATURES",
            f"Missing gold_usd_close: {missing_market['gold_usd_close']}",
            f"Missing gold_usd_open: {missing_market['gold_usd_open']}",
            f"Missing gold_usd_high: {missing_market['gold_usd_high']}",
            f"Missing gold_usd_low: {missing_market['gold_usd_low']}",
            "",
            "USD/INR FEATURES",
            f"Missing usdinr_close: {missing_market['usdinr_close']}",
            f"Missing usdinr_open: {missing_market['usdinr_open']}",
            f"Missing usdinr_high: {missing_market['usdinr_high']}",
            f"Missing usdinr_low: {missing_market['usdinr_low']}",
            "",
            f"Rows containing market data: {validation['market_rows_present']} ({market_percentage:.2f}%)",
            f"Original IBJA rows: {original_ibja_rows}",
            "Missing values were preserved; no fill or estimation was performed.",
            "",
            "Missing-value summary:",
            *[f"{column}: {count}" for column, count in validation["missing_values"].items()],
            "",
        ]
    )


def main() -> None:
    ibja, market = load_inputs()
    original_ibja_rows = len(ibja)

    # The IBJA table is the left side so no observed target row can be created or lost.
    master = ibja.merge(market, on="date", how="left", validate="many_to_one")
    target_column = "gold_999_avg" if "gold_999_avg" in master.columns else "gold_999_average"
    if target_column not in master.columns:
        raise ValueError("IBJA input must contain gold_999_avg or gold_999_average.")
    master["target_gold_999"] = pd.to_numeric(master[target_column], errors="coerce")

    master = master.sort_values("date").drop_duplicates(subset=["date"], keep="first")
    validation = validate_master(master)
    master["date"] = master["date"].dt.strftime("%Y-%m-%d")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    master.to_csv(OUTPUT_PATH, index=False)
    REPORT_PATH.write_text(format_report(validation, master.assign(date=pd.to_datetime(master["date"])), original_ibja_rows), encoding="utf-8")

    print("MASTER DATASET VALIDATION")
    print(f"Rows: {validation['rows']}")
    print(f"Earliest date: {validation['earliest_date']}")
    print(f"Latest date: {validation['latest_date']}")
    print(f"Duplicate dates: {validation['duplicate_dates']}")
    print(f"\nIBJA TARGET\nMissing target values: {validation['missing_target']}")
    print(f"Minimum target: {validation['minimum_target']}")
    print(f"Maximum target: {validation['maximum_target']}")
    print("\nINTERNATIONAL GOLD FEATURES")
    for column in ("gold_usd_close", "gold_usd_open", "gold_usd_high", "gold_usd_low"):
        print(f"Missing {column}: {validation['missing_market'][column]}")
    print("\nUSD/INR FEATURES")
    for column in ("usdinr_close", "usdinr_open", "usdinr_high", "usdinr_low"):
        print(f"Missing {column}: {validation['missing_market'][column]}")
    print(f"\nRows containing market data: {validation['market_rows_present']} ({validation['market_rows_present'] / len(master) * 100:.2f}%)")
    print(f"\nOutput: {OUTPUT_PATH.relative_to(PROJECT_ROOT)}")
    print(f"Validation report: {REPORT_PATH.relative_to(PROJECT_ROOT)}")
    print("\nFIRST 10 ROWS")
    print(master.head(10).to_string(index=False))
    print("\nLAST 10 ROWS")
    print(master.tail(10).to_string(index=False))
    print(f"\nDataset shape: {master.shape}")
    print(f"Column names: {list(master.columns)}")
    print("\nMISSING-VALUE SUMMARY")
    print(master.isna().sum().to_string())


if __name__ == "__main__":
    main()