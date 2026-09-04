"""Download supporting international gold and USD/INR market data from Yahoo Finance."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import yfinance as yf


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
START_DATE = pd.Timestamp("2025-09-02")
END_DATE = pd.Timestamp("2026-09-02")


def download_ticker(ticker: str) -> pd.DataFrame:
    """Download one ticker, using an exclusive end boundary after the target date."""
    try:
        data = yf.download(
            ticker,
            start=START_DATE.strftime("%Y-%m-%d"),
            end=(END_DATE + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
            auto_adjust=False,
            progress=False,
            threads=False,
        )
    except Exception as error:
        raise RuntimeError(f"Yahoo Finance request failed for {ticker}: {error}") from error

    if data.empty:
        raise RuntimeError(f"Yahoo Finance returned no data for {ticker}.")

    # yfinance may return a MultiIndex even for a single ticker.
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    data = data.reset_index()
    date_column = "Date" if "Date" in data.columns else "Datetime"
    data["date"] = pd.to_datetime(data[date_column], errors="coerce", utc=True).dt.tz_localize(None).dt.normalize()
    data = data.dropna(subset=["date"])
    data = data[data["date"].between(START_DATE, END_DATE)]
    data = data.drop_duplicates(subset=["date"], keep="last").sort_values("date")
    return data


def prepare_dataset(data: pd.DataFrame, columns: dict[str, str]) -> pd.DataFrame:
    """Select, rename, normalize, and numerically coerce the requested fields."""
    selected = data[["date", *columns]].rename(columns=columns).copy()
    selected["date"] = selected["date"].dt.strftime("%Y-%m-%d")
    for column in columns.values():
        selected[column] = pd.to_numeric(selected[column], errors="coerce")
    return selected.sort_values("date").drop_duplicates(subset=["date"], keep="last")


def print_validation(label: str, data: pd.DataFrame) -> None:
    """Print a consistent validation summary without filling missing values."""
    dates = pd.to_datetime(data["date"], errors="coerce")
    duplicate_dates = int(data["date"].duplicated().sum())
    print(f"\n{label}")
    print(f"Rows: {len(data)}")
    print(f"Date range: {dates.min().date() if dates.notna().any() else 'N/A'} to {dates.max().date() if dates.notna().any() else 'N/A'}")
    print(f"Missing values: {int(data.isna().sum().sum())}")
    print(f"Duplicate dates: {duplicate_dates}")


def main() -> None:
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    gold_raw = download_ticker("GC=F")
    gold = prepare_dataset(
        gold_raw,
        {
            "Open": "gold_usd_open",
            "High": "gold_usd_high",
            "Low": "gold_usd_low",
            "Close": "gold_usd_close",
            "Volume": "gold_usd_volume",
        },
    )

    usdinr_raw = download_ticker("USDINR=X")
    usdinr = prepare_dataset(
        usdinr_raw,
        {
            "Open": "usdinr_open",
            "High": "usdinr_high",
            "Low": "usdinr_low",
            "Close": "usdinr_close",
        },
    )

    gold_path = RAW_DATA_DIR / "international_gold_gc_f.csv"
    usdinr_path = RAW_DATA_DIR / "usdinr_daily.csv"
    aligned_path = RAW_DATA_DIR / "international_market_data.csv"
    gold.to_csv(gold_path, index=False)
    usdinr.to_csv(usdinr_path, index=False)

    # Use an outer join so a market holiday in either source remains visible as missing data.
    aligned = gold.merge(usdinr, on="date", how="outer", validate="one_to_one").sort_values("date")
    aligned.to_csv(aligned_path, index=False)

    print_validation("INTERNATIONAL GOLD DATA", gold)
    print_validation("USDINR DATA", usdinr)
    print_validation("ALIGNED MARKET DATA", aligned)
    print(f"\nOutput files:\n- {gold_path.relative_to(PROJECT_ROOT)}\n- {usdinr_path.relative_to(PROJECT_ROOT)}\n- {aligned_path.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()