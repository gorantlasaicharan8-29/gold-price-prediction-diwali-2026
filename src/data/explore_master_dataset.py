"""Exploratory analysis and visualization for the gold master dataset."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


PROJECT_ROOT = Path(__file__).resolve().parents[2]
INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "gold_master_dataset.csv"
REPORTS_DIR = PROJECT_ROOT / "reports"

STATISTICS_COLUMNS = [
    "gold_999_average",
    "target_gold_999",
    "gold_usd_open",
    "gold_usd_high",
    "gold_usd_low",
    "gold_usd_close",
    "usdinr_open",
    "usdinr_high",
    "usdinr_low",
    "usdinr_close",
]


def load_dataset() -> pd.DataFrame:
    """Load the master dataset without changing its stored values."""
    data = pd.read_csv(INPUT_PATH)
    data["date"] = pd.to_datetime(data["date"], errors="raise")
    return data.sort_values("date").reset_index(drop=True)


def plot_line(data: pd.DataFrame, columns: list[str], labels: list[str], title: str, ylabel: str, output_path: Path) -> None:
    """Create and save a date-based line chart while preserving missing values."""
    figure, axis = plt.subplots(figsize=(12, 6))
    for column, label in zip(columns, labels):
        axis.plot(data["date"], data[column], label=label, linewidth=1.8)
    axis.set_title(title)
    axis.set_xlabel("Date")
    axis.set_ylabel(ylabel)
    if len(columns) > 1:
        axis.legend()
    figure.tight_layout()
    figure.savefig(output_path, dpi=150)
    plt.close(figure)


def outlier_rows(data: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Return IQR bounds and counts without deleting or modifying observations."""
    results = []
    for column in columns:
        values = data[column].dropna()
        first_quartile = values.quantile(0.25)
        third_quartile = values.quantile(0.75)
        iqr = third_quartile - first_quartile
        lower_bound = first_quartile - 1.5 * iqr
        upper_bound = third_quartile + 1.5 * iqr
        outlier_count = int(((values < lower_bound) | (values > upper_bound)).sum())
        results.append(
            {
                "variable": column,
                "lower_bound": lower_bound,
                "upper_bound": upper_bound,
                "number_of_potential_outliers": outlier_count,
            }
        )
    return pd.DataFrame(results)


def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    data = load_dataset()

    duplicate_dates = int(data["date"].duplicated().sum())
    missing_summary = data.isna().sum()
    statistics = data[STATISTICS_COLUMNS].describe().T
    statistics = statistics.rename(index={"gold_999_average": "gold_999_avg"})
    statistics.to_csv(REPORTS_DIR / "descriptive_statistics.csv")

    plot_line(
        data,
        ["target_gold_999"],
        ["target_gold_999"],
        "IBJA Gold 999 Average Price Trend",
        "Gold Price (INR per 10g)",
        REPORTS_DIR / "gold_price_trend.png",
    )
    plot_line(
        data,
        ["gold_999_am", "gold_999_pm"],
        ["AM", "PM"],
        "IBJA Gold 999 AM vs PM Prices",
        "Gold Price (INR per 10g)",
        REPORTS_DIR / "gold_am_pm_comparison.png",
    )
    plot_line(
        data,
        ["gold_usd_close"],
        ["Gold USD Close"],
        "International Gold Price Trend",
        "Gold Price (USD)",
        REPORTS_DIR / "international_gold_trend.png",
    )
    plot_line(
        data,
        ["usdinr_close"],
        ["USD/INR Close"],
        "USD/INR Exchange Rate Trend",
        "USD/INR", 
        REPORTS_DIR / "usdinr_trend.png",
    )

    numeric_data = data.select_dtypes(include="number")
    correlation = numeric_data.corr(method="pearson")
    correlation.to_csv(REPORTS_DIR / "correlation_matrix.csv")
    figure, axis = plt.subplots(figsize=(13, 10))
    sns.heatmap(correlation, cmap="vlag", center=0, annot=True, fmt=".2f", square=True, ax=axis)
    axis.set_title("Gold Market Feature Correlation Matrix")
    figure.tight_layout()
    figure.savefig(REPORTS_DIR / "correlation_heatmap.png", dpi=150)
    plt.close(figure)

    # These percentage changes are temporary EDA calculations, not saved model features.
    movement = pd.DataFrame(
        {
            "target_gold_999_pct_change": data["target_gold_999"].pct_change() * 100,
            "gold_usd_close_pct_change": data["gold_usd_close"].pct_change() * 100,
            "usdinr_close_pct_change": data["usdinr_close"].pct_change() * 100,
        }
    )
    gold_movement = movement["target_gold_999_pct_change"].dropna()
    movement_statistics = {
        "mean": gold_movement.mean(),
        "std": gold_movement.std(),
        "min": gold_movement.min(),
        "max": gold_movement.max(),
    }

    outliers = outlier_rows(data, ["target_gold_999", "gold_usd_close", "usdinr_close"])
    outliers.to_csv(REPORTS_DIR / "outlier_analysis.csv", index=False)

    target_gold_correlation = correlation.get("target_gold_999", pd.Series(dtype=float))
    report_lines = [
        "EDA REPORT",
        "=========",
        "",
        "1. DATASET OVERVIEW",
        f"Dataset shape: {data.shape}",
        f"Number of rows: {len(data)}",
        f"Number of columns: {len(data.columns) - 1}",
        f"Duplicate dates: {duplicate_dates}",
        "",
        "2. DATE COVERAGE",
        f"Earliest date: {data['date'].min().strftime('%Y-%m-%d')}",
        f"Latest date: {data['date'].max().strftime('%Y-%m-%d')}",
        "",
        "3. MISSING-VALUE SUMMARY",
        missing_summary.to_string(),
        "",
        "4. DESCRIPTIVE STATISTICS SUMMARY",
        statistics.to_string(),
        "",
        "5. CORRELATION FINDINGS",
        f"target_gold_999 vs gold_usd_close: {target_gold_correlation.get('gold_usd_close', float('nan')):.6f}",
        f"target_gold_999 vs usdinr_close: {target_gold_correlation.get('usdinr_close', float('nan')):.6f}",
        f"target_gold_999 vs gold_usd_open: {target_gold_correlation.get('gold_usd_open', float('nan')):.6f}",
        f"target_gold_999 vs gold_usd_high: {target_gold_correlation.get('gold_usd_high', float('nan')):.6f}",
        f"target_gold_999 vs gold_usd_low: {target_gold_correlation.get('gold_usd_low', float('nan')):.6f}",
        "Correlations are Pearson associations based on pairwise available observations and do not establish causation.",
        "",
        "6. DAILY MOVEMENT STATISTICS",
        f"Mean daily gold percentage change: {movement_statistics['mean']:.6f}%",
        f"Standard deviation of daily gold percentage change: {movement_statistics['std']:.6f}%",
        f"Minimum daily gold percentage change: {movement_statistics['min']:.6f}%",
        f"Maximum daily gold percentage change: {movement_statistics['max']:.6f}%",
        "",
        "7. OUTLIER ANALYSIS",
        outliers.to_string(index=False),
        "",
        "8. IMPORTANT OBSERVATIONS",
        "The dataset contains IBJA target observations from the available source period; missing market values remain missing.",
        f"International gold values are available for {data['gold_usd_close'].notna().sum()} of {len(data)} rows.",
        f"USD/INR values are available for {data['usdinr_close'].notna().sum()} of {len(data)} rows.",
        "Potential outliers are identified statistically and were not removed or modified.",
        "The descriptive statistics and correlations reflect available observations only.",
        "",
    ]
    (REPORTS_DIR / "eda_report.txt").write_text("\n".join(report_lines), encoding="utf-8")

    print("EDA REPORT")
    print("==========")
    print(f"\nDataset shape: {data.shape}")
    print(f"Number of rows: {len(data)}")
    print(f"Number of columns: {len(data.columns) - 1}")
    print(f"\nDate range: {data['date'].min().date()} to {data['date'].max().date()}")
    print(f"Earliest date: {data['date'].min().date()}")
    print(f"Latest date: {data['date'].max().date()}")
    print(f"\nDuplicate dates: {duplicate_dates}")
    print("\nColumn data types:")
    print(data.dtypes.to_string())
    print("\nComplete missing-value summary:")
    print(missing_summary.to_string())
    print("\nDaily gold percentage change statistics:")
    for name, value in movement_statistics.items():
        print(f"{name}: {value:.6f}%")
    print("\nEDA COMPLETE")
    print("Files created:")
    for filename in (
        "descriptive_statistics.csv",
        "gold_price_trend.png",
        "gold_am_pm_comparison.png",
        "international_gold_trend.png",
        "usdinr_trend.png",
        "correlation_matrix.csv",
        "correlation_heatmap.png",
        "outlier_analysis.csv",
        "eda_report.txt",
    ):
        print(REPORTS_DIR.joinpath(filename).relative_to(PROJECT_ROOT))


if __name__ == "__main__":
    main()