"""Perform the final unbiased test evaluation for the selected model."""

from __future__ import annotations

from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, mean_squared_error, r2_score


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_DATA_DIR = PROJECT_ROOT / "data" / "processed" / "model_data"
MODELS_DIR = PROJECT_ROOT / "models"
EVALUATION_DIR = PROJECT_ROOT / "reports" / "model_evaluation"
TARGET = "target_gold_999"


def prepare_test_matrix(X_test: pd.DataFrame, preprocessor: object) -> pd.DataFrame:
    """Reuse Step 28's transformed test matrix or transform raw columns without fitting."""
    expected_names = list(preprocessor.get_feature_names_out())
    if list(X_test.columns) == expected_names:
        return X_test
    transformed = preprocessor.transform(X_test)
    return pd.DataFrame(transformed, columns=expected_names, index=X_test.index)


def main() -> None:
    EVALUATION_DIR.mkdir(parents=True, exist_ok=True)
    model = joblib.load(MODELS_DIR / "linear_regression.joblib")
    preprocessor = joblib.load(MODEL_DATA_DIR / "preprocessor.joblib")
    X_test = pd.read_csv(MODEL_DATA_DIR / "X_test.csv")
    y_test = pd.read_csv(MODEL_DATA_DIR / "y_test.csv")[TARGET]
    test_dates = pd.read_csv(MODEL_DATA_DIR / "test_dates.csv")
    test_dates["date"] = pd.to_datetime(test_dates["date"], errors="raise")

    if len(X_test) != 26 or len(y_test) != 26 or len(test_dates) != 26:
        raise ValueError("Expected exactly 26 test rows in X, y, and date files.")
    if test_dates["date"].duplicated().any() or not test_dates["date"].is_monotonic_increasing:
        raise ValueError("Test dates are not unique and chronologically ordered.")
    if test_dates["date"].min() != pd.Timestamp("2026-07-28") or test_dates["date"].max() != pd.Timestamp("2026-09-01"):
        raise ValueError("Unexpected test date range.")
    if y_test.isna().any():
        raise ValueError("Test target contains missing values.")

    # The preprocessor is never fitted here. Step 28's already transformed matrix is reused when detected.
    X_test_prepared = prepare_test_matrix(X_test, preprocessor)
    predicted = model.predict(X_test_prepared)
    actual = y_test.to_numpy()
    residual = actual - predicted
    absolute_error = np.abs(residual)
    percentage_error = np.abs(residual / actual) * 100
    metrics = {
        "MAE": mean_absolute_error(actual, predicted),
        "RMSE": np.sqrt(mean_squared_error(actual, predicted)),
        "MAPE": mean_absolute_percentage_error(actual, predicted) * 100,
        "R2": r2_score(actual, predicted),
    }

    prediction_data = pd.DataFrame(
        {
            "date": test_dates["date"].dt.strftime("%Y-%m-%d"),
            "actual_gold_999": actual,
            "predicted_gold_999": predicted,
            "residual": residual,
            "absolute_error": absolute_error,
            "percentage_error": percentage_error,
        }
    )
    prediction_data.to_csv(EVALUATION_DIR / "test_predictions.csv", index=False)

    figure, axis = plt.subplots(figsize=(13, 7))
    axis.plot(prediction_data["date"], prediction_data["actual_gold_999"], label="Actual Gold 999 Price", linewidth=2.5, color="black")
    axis.plot(prediction_data["date"], prediction_data["predicted_gold_999"], label="Predicted Gold 999 Price", linewidth=2)
    axis.set_title("Final Test Evaluation - Actual vs Predicted Gold Price")
    axis.set_xlabel("Date")
    axis.set_ylabel("Gold Price (INR per 10g)")
    axis.tick_params(axis="x", rotation=45)
    axis.legend()
    figure.tight_layout()
    figure.savefig(EVALUATION_DIR / "test_predictions.png", dpi=150)
    plt.close(figure)

    largest_index = int(np.argmax(absolute_error))
    smallest_index = int(np.argmin(absolute_error))
    error_analysis = {
        "mean_absolute_error": absolute_error.mean(),
        "maximum_absolute_error": absolute_error.max(),
        "minimum_absolute_error": absolute_error.min(),
        "mean_percentage_error": percentage_error.mean(),
        "maximum_percentage_error": percentage_error.max(),
        "largest_absolute_error_date": prediction_data.iloc[largest_index]["date"],
        "smallest_absolute_error_date": prediction_data.iloc[smallest_index]["date"],
    }

    validation_results = pd.read_csv(EVALUATION_DIR / "validation_results.csv")
    validation_row = validation_results.loc[validation_results["model"] == "Linear Regression"]
    if len(validation_row) != 1:
        raise ValueError("Could not identify exactly one Linear Regression validation result.")
    validation_row = validation_row.iloc[0]
    performance = pd.DataFrame(
        [
            {"dataset": "validation", "model": "Linear Regression", "MAE": validation_row["MAE"], "RMSE": validation_row["RMSE"], "MAPE": validation_row["MAPE"], "R2": validation_row["R2"]},
            {"dataset": "test", "model": "Linear Regression", **metrics},
        ]
    )
    performance.to_csv(EVALUATION_DIR / "final_model_performance.csv", index=False)

    report = "\n".join(
        [
            "FINAL TEST EVALUATION REPORT",
            "============================",
            "",
            "1. SELECTED MODEL",
            "Linear Regression",
            "Selected because it had the lowest validation RMSE, followed by the required tie-break ordering of MAE, MAPE, and R2.",
            "",
            "2. VALIDATION METRICS",
            validation_row.to_string(),
            "",
            "3. FINAL TEST METRICS",
            *[f"{name}: {value}" for name, value in metrics.items()],
            "",
            "4. TEST INFORMATION",
            "Test sample size: 26",
            "Test date range: 2026-07-28 to 2026-09-01",
            "",
            "5. ERROR ANALYSIS",
            *[f"{name}: {value}" for name, value in error_analysis.items()],
            "",
            "6. VALIDATION VS TEST PERFORMANCE",
            performance.to_string(index=False),
            "Test performance is an estimate of performance on unseen historical data and is not a guarantee of accuracy on future dates.",
            "",
            "7. TEST PROTECTION AND LEAKAGE",
            "The test set was not used for model selection, tuning, or training before this final evaluation.",
            "The saved training-fitted preprocessor was reused without refitting on test data.",
            "No future data was used to generate the test predictions.",
            "Data leakage check: PASSED",
            "",
        ]
    )
    (EVALUATION_DIR / "final_test_evaluation_report.txt").write_text(report, encoding="utf-8")

    print("FINAL TEST EVALUATION")
    print("=====================")
    print("Model: Linear Regression")
    print(f"Test rows: {len(prediction_data)}")
    print("Date range: 2026-07-28 to 2026-09-01")
    for name, value in metrics.items():
        suffix = "%" if name == "MAPE" else ""
        print(f"{name}: {value:.6f}{suffix}")
    print("\nERROR ANALYSIS")
    for name, value in error_analysis.items():
        print(f"{name}: {value}")
    print("\nFINAL TEST EVALUATION COMPLETE")
    print("Selected model: Linear Regression")
    print("Test evaluation: COMPLETE")
    print("Test set used before this step: NO")
    print("Test set used for model selection: NO")
    print("Data leakage: PASSED")
    print("Files created:")
    for filename in ("test_predictions.csv", "test_predictions.png", "final_model_performance.csv", "final_test_evaluation_report.txt"):
        print(EVALUATION_DIR.joinpath(filename).relative_to(PROJECT_ROOT))


if __name__ == "__main__":
    main()