"""Create leakage-aware time-series features from the gold master dataset."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "gold_master_dataset.csv"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "gold_feature_dataset.csv"
REPORT_PATH = PROJECT_ROOT / "reports" / "feature_engineering_report.txt"
DIWALI_DATE = pd.Timestamp("2026-11-08")


def load_master_dataset() -> pd.DataFrame:
    """Load and chronologically order the master data without changing source files."""
    data = pd.read_csv(INPUT_PATH)
    data["date"] = pd.to_datetime(data["date"], errors="raise")
    if data["date"].duplicated().any():
        raise ValueError("The master dataset contains duplicate dates.")
    return data.sort_values("date").reset_index(drop=True)


def create_features(master: pd.DataFrame) -> pd.DataFrame:
    """Build features from information available before each target observation."""
    features = master.copy()
    target = features["target_gold_999"]

    # Calendar values are known in advance and do not use market observations.
    features["day_of_week"] = features["date"].dt.dayofweek
    features["day_of_month"] = features["date"].dt.day
    features["month"] = features["date"].dt.month
    features["quarter"] = features["date"].dt.quarter
    features["day_of_year"] = features["date"].dt.dayofyear
    features["week_of_year"] = features["date"].dt.isocalendar().week.astype("int64")
    features["is_month_start"] = features["date"].dt.is_month_start.astype("int64")
    features["is_month_end"] = features["date"].dt.is_month_end.astype("int64")
    features["days_to_diwali"] = (DIWALI_DATE - features["date"]).dt.days
    features["is_near_diwali"] = features["days_to_diwali"].abs().le(30).astype("int64")

    # Shift first: every target-derived feature uses observations strictly before today.
    historical_target = target.shift(1)
    for lag in (1, 2, 3, 5, 7, 14):
        features[f"gold_lag_{lag}"] = target.shift(lag)
    for window in (3, 7, 14, 30):
        features[f"gold_ma_{window}"] = historical_target.rolling(window=window, min_periods=window).mean()

    target_returns = historical_target.pct_change() * 100
    for period in (1, 3, 7):
        features[f"gold_return_{period}d"] = historical_target.pct_change(periods=period) * 100
    for window in (7, 14, 30):
        features[f"gold_volatility_{window}"] = target_returns.rolling(window=window, min_periods=window).std()

    # Market series are retained as observed. Their derived histories never fill missing prices.
    for period in (1, 3, 7):
        features[f"gold_usd_return_{period}d"] = features["gold_usd_close"].pct_change(periods=period) * 100
        features[f"usdinr_return_{period}d"] = features["usdinr_close"].pct_change(periods=period) * 100
    for window in (7, 14):
        features[f"gold_usd_volatility_{window}"] = features["gold_usd_close"].pct_change().rolling(window=window, min_periods=window).std() * 100
        features[f"usdinr_volatility_{window}"] = features["usdinr_close"].pct_change().rolling(window=window, min_periods=window).std() * 100
    features["gold_inr_proxy"] = features["gold_usd_close"] * features["usdinr_close"]

    # Exclude same-day IBJA source columns from predictors because they directly reveal the target.
    features = features.drop(columns=["gold_999_am", "gold_999_pm", "gold_999_average"])

    return features


def leakage_check(features: pd.DataFrame) -> tuple[bool, list[str]]:
    """Check the construction invariants for target-derived features."""
    issues = []
    target = features["target_gold_999"]
    expected_lags = {
        "gold_lag_1": target.shift(1),
        "gold_lag_2": target.shift(2),
        "gold_lag_3": target.shift(3),
        "gold_lag_5": target.shift(5),
        "gold_lag_7": target.shift(7),
        "gold_lag_14": target.shift(14),
    }
    for name, expected in expected_lags.items():
        if not features[name].equals(expected):
            issues.append(f"{name} does not equal the corresponding prior target values.")
    historical_target = target.shift(1)
    for window in (3, 7, 14, 30):
        expected = historical_target.rolling(window=window, min_periods=window).mean()
        if not features[f"gold_ma_{window}"].equals(expected):
            issues.append(f"gold_ma_{window} is not shifted before rolling.")
    if features["target_gold_999"].name in features.drop(columns=["target_gold_999"]).columns:
        issues.append("Target column was duplicated among feature columns.")
    direct_target_columns = {"gold_999_am", "gold_999_pm", "gold_999_average"}
    leaked_columns = direct_target_columns.intersection(features.columns)
    if leaked_columns:
        issues.append(f"Direct same-day target source columns remain: {sorted(leaked_columns)}.")
    return not issues, issues


def build_report(master: pd.DataFrame, features: pd.DataFrame, missing: pd.Series, leakage_passed: bool, leakage_issues: list[str]) -> str:
    """Create a plain-text audit of feature construction and missingness."""
    feature_columns = [column for column in features.columns if column not in {"date", "target_gold_999"}]
    warmup_columns = [column for column in feature_columns if column.startswith(("gold_lag_", "gold_ma_", "gold_return_", "gold_volatility_"))]
    warmup_rows = int(features[warmup_columns].isna().any(axis=1).sum())
    lines = [
        "FEATURE ENGINEERING REPORT",
        "==========================",
        "",
        f"Original rows: {len(master)}",
        f"Feature dataset rows: {len(features)}",
        f"Rows removed: {len(master) - len(features)}",
        f"Rows with insufficient target history: {warmup_rows}",
        f"Original columns: {len(master.columns)}",
        f"Feature columns: {len(features.columns)}",
        f"Date range: {features['date'].min().strftime('%Y-%m-%d')} to {features['date'].max().strftime('%Y-%m-%d')}",
        f"Target missing values: {int(features['target_gold_999'].isna().sum())}",
        "",
        "MISSING VALUES BY FEATURE",
    ]
    lines.extend(f"{column}: {int(count)}" for column, count in missing.items() if count > 0)
    if not any(missing > 0):
        lines.append("None")
    lines.extend(
        [
            "",
            "DATA LEAKAGE CHECK",
            f"Status: {'PASSED' if leakage_passed else 'FAILED'}",
            "Target-derived lags and rolling averages use shifted historical observations.",
            "No target values were filled, shifted into the target column, or used without shifting.",
            "",
            "FEATURE COLUMNS",
            *feature_columns,
        ]
    )
    if leakage_issues:
        lines.extend(["", "Leakage issues:", *leakage_issues])
    return "\n".join(lines) + "\n"


def main() -> None:
    master = load_master_dataset()
    features = create_features(master)
    leakage_passed, leakage_issues = leakage_check(features)
    if not leakage_passed:
        raise RuntimeError("Data leakage detected: " + "; ".join(leakage_issues))

    missing = features.isna().sum()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    features.to_csv(OUTPUT_PATH, index=False, date_format="%Y-%m-%d")
    REPORT_PATH.write_text(build_report(master, features, missing, leakage_passed, leakage_issues), encoding="utf-8")

    print("FEATURE ENGINEERING REPORT")
    print("==========================")
    print(f"Original rows: {len(master)}")
    print(f"Feature dataset rows: {len(features)}")
    print(f"Original columns: {len(master.columns)}")
    print(f"Feature columns: {len(features.columns)}")
    print(f"Date range: {features['date'].min().date()} to {features['date'].max().date()}")
    print(f"Target missing values: {int(features['target_gold_999'].isna().sum())}")
    print("\nMissing values by feature:")
    for column, count in missing.items():
        if count > 0:
            print(f"{column}: {count}")
    print("\nDATA LEAKAGE CHECK: PASSED")
    print("\nFEATURE COLUMNS:")
    print("\n".join(column for column in features.columns if column not in {"date", "target_gold_999"}))
    print(f"\nOutput: {OUTPUT_PATH.relative_to(PROJECT_ROOT)}")
    print(f"Report: {REPORT_PATH.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()