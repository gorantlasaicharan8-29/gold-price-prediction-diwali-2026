"""Train and compare regression models using a chronological validation split."""

from __future__ import annotations

from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, mean_squared_error, r2_score
from xgboost import XGBRegressor


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_DATA_DIR = PROJECT_ROOT / "data" / "processed" / "model_data"
MODELS_DIR = PROJECT_ROOT / "models"
EVALUATION_DIR = PROJECT_ROOT / "reports" / "model_evaluation"
TARGET = "target_gold_999"


def load_split(name: str) -> pd.DataFrame:
    return pd.read_csv(MODEL_DATA_DIR / f"{name}.csv")


def validate_dates(train_dates: pd.DataFrame, validation_dates: pd.DataFrame, test_dates: pd.DataFrame) -> None:
    """Ensure the saved split boundaries are strictly chronological."""
    date_frames = [frame.assign(date=pd.to_datetime(frame["date"], errors="raise")) for frame in (train_dates, validation_dates, test_dates)]
    if any(frame["date"].duplicated().any() for frame in date_frames):
        raise ValueError("Duplicate dates found in a split.")
    if not (date_frames[0]["date"].max() < date_frames[1]["date"].min() < date_frames[1]["date"].max() < date_frames[2]["date"].min()):
        raise ValueError("Train, validation, and test splits are not strictly chronological.")


def prepare_matrix(X: pd.DataFrame, preprocessor: object) -> pd.DataFrame:
    """Reuse Step 28 matrices or transform raw matrices with the fitted preprocessor."""
    expected_names = list(preprocessor.get_feature_names_out())
    if list(X.columns) == expected_names:
        return X
    transformed = preprocessor.transform(X)
    return pd.DataFrame(transformed, columns=expected_names, index=X.index)


def build_models() -> dict[str, object]:
    return {
        "Linear Regression": LinearRegression(),
        "Random Forest": RandomForestRegressor(
            n_estimators=300,
            max_depth=None,
            min_samples_split=2,
            min_samples_leaf=1,
            random_state=42,
            n_jobs=-1,
        ),
        "Gradient Boosting": GradientBoostingRegressor(
            n_estimators=200,
            learning_rate=0.05,
            max_depth=3,
            min_samples_split=2,
            min_samples_leaf=1,
            random_state=42,
        ),
        "XGBoost": XGBRegressor(
            n_estimators=300,
            learning_rate=0.05,
            max_depth=4,
            subsample=0.8,
            colsample_bytree=0.8,
            objective="reg:squarederror",
            random_state=42,
            n_jobs=-1,
        ),
    }


def metrics(actual: pd.Series, predicted: np.ndarray) -> dict[str, float]:
    return {
        "MAE": mean_absolute_error(actual, predicted),
        "RMSE": np.sqrt(mean_squared_error(actual, predicted)),
        "MAPE": mean_absolute_percentage_error(actual, predicted) * 100,
        "R2": r2_score(actual, predicted),
    }


def main() -> None:
    EVALUATION_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    X_train = load_split("X_train")
    X_validation = load_split("X_validation")
    X_test = load_split("X_test")
    y_train = load_split("y_train")[TARGET]
    y_validation = load_split("y_validation")[TARGET]
    y_test = load_split("y_test")[TARGET]
    train_dates = load_split("train_dates")
    validation_dates = load_split("validation_dates")
    test_dates = load_split("test_dates")
    validate_dates(train_dates, validation_dates, test_dates)

    if (len(X_train), len(X_validation), len(X_test)) != (117, 25, 26):
        raise ValueError("Unexpected split sizes.")
    if any(series.isna().any() for series in (y_train, y_validation, y_test)):
        raise ValueError("Target values must not be missing.")

    preprocessor = joblib.load(MODEL_DATA_DIR / "preprocessor.joblib")
    X_train = prepare_matrix(X_train, preprocessor)
    X_validation = prepare_matrix(X_validation, preprocessor)
    X_test = prepare_matrix(X_test, preprocessor)
    models = build_models()
    predictions: dict[str, np.ndarray] = {}
    results = []

    for name, model in models.items():
        model.fit(X_train, y_train)
        validation_prediction = model.predict(X_validation)
        predictions[name] = validation_prediction
        results.append({"model": name, **metrics(y_validation, validation_prediction)})
        joblib.dump(model, MODELS_DIR / f"{name.lower().replace(' ', '_')}.joblib")

    validation_results = pd.DataFrame(results).sort_values(["RMSE", "MAE", "MAPE", "R2"], ascending=[True, True, True, False]).reset_index(drop=True)
    validation_results.to_csv(EVALUATION_DIR / "validation_results.csv", index=False)
    best_model = validation_results.iloc[0]["model"]
    (MODELS_DIR / "best_validation_model.txt").write_text(f"{best_model}\n", encoding="utf-8")

    validation_prediction_rows = {
        "date": pd.to_datetime(validation_dates["date"]).dt.strftime("%Y-%m-%d"),
        "actual_gold_999": y_validation.to_numpy(),
        "linear_regression_prediction": predictions["Linear Regression"],
        "random_forest_prediction": predictions["Random Forest"],
        "gradient_boosting_prediction": predictions["Gradient Boosting"],
        "xgboost_prediction": predictions["XGBoost"],
    }
    pd.DataFrame(validation_prediction_rows).to_csv(EVALUATION_DIR / "validation_predictions.csv", index=False)

    figure, axis = plt.subplots(figsize=(13, 7))
    axis.plot(validation_prediction_rows["date"], y_validation, label="Actual Gold Price", linewidth=2.5, color="black")
    for name, prediction in predictions.items():
        axis.plot(validation_prediction_rows["date"], prediction, label=name)
    axis.set_title("Validation: Actual vs Model Predictions")
    axis.set_xlabel("Date")
    axis.set_ylabel("Gold Price (INR per 10g)")
    axis.tick_params(axis="x", rotation=45)
    axis.legend()
    figure.tight_layout()
    figure.savefig(EVALUATION_DIR / "validation_predictions.png", dpi=150)
    plt.close(figure)

    residual_rows = []
    for name, prediction in predictions.items():
        residual_rows.extend(
            {
                "date": current_date,
                "actual_gold_999": actual,
                "model": name,
                "prediction": predicted,
                "residual": actual - predicted,
            }
            for current_date, actual, predicted in zip(validation_prediction_rows["date"], y_validation, prediction)
        )
    pd.DataFrame(residual_rows).to_csv(EVALUATION_DIR / "validation_residuals.csv", index=False)

    importance_files = {
        "Random Forest": "random_forest_feature_importance.csv",
        "Gradient Boosting": "gradient_boosting_feature_importance.csv",
        "XGBoost": "xgboost_feature_importance.csv",
    }
    for name, filename in importance_files.items():
        importance = pd.DataFrame({"feature": X_train.columns, "importance": models[name].feature_importances_}).sort_values("importance", ascending=False)
        importance.to_csv(EVALUATION_DIR / filename, index=False)

    ranking = validation_results.copy()
    report_lines = [
        "MODEL COMPARISON REPORT",
        "=======================",
        "",
        "1. MODELS TRAINED",
        *models.keys(),
        "",
        "2. TRAINING DATASET INFORMATION",
        f"Rows: {len(X_train)}",
        f"Date range: {pd.to_datetime(train_dates['date']).min().date()} to {pd.to_datetime(train_dates['date']).max().date()}",
        "Training used only X_train and y_train.",
        "",
        "3. VALIDATION DATASET INFORMATION",
        f"Rows: {len(X_validation)}",
        f"Date range: {pd.to_datetime(validation_dates['date']).min().date()} to {pd.to_datetime(validation_dates['date']).max().date()}",
        "",
        "4. VALIDATION METRICS",
        validation_results.to_string(index=False),
        "",
        "5. RANKING",
        ranking[["model", "RMSE", "MAE", "MAPE", "R2"]].to_string(index=False),
        f"Best validation model: {best_model}",
        "",
        "6. FEATURE IMPORTANCE SUMMARY",
        "Feature importance files were generated for Random Forest, Gradient Boosting, and XGBoost.",
        "",
        "7. TEST DATA PROTECTION",
        "Test data was loaded only for size, target completeness, and chronological integrity checks.",
        "Test predictions and test metrics were not generated.",
        "The test set was not used for model selection or tuning.",
        "",
    ]
    (EVALUATION_DIR / "model_comparison_report.txt").write_text("\n".join(report_lines), encoding="utf-8")

    print("VALIDATION MODEL COMPARISON")
    print(validation_results.to_string(index=False))
    print(f"\nBEST VALIDATION MODEL:\n{best_model}")
    print("\nMODEL TRAINING COMPLETE")
    print("Models trained: 4")
    print("Validation evaluation: COMPLETE")
    print("Test set used: NO")
    print(f"Best validation model: {best_model}")
    print("Model files created: 4 model joblib files and best_validation_model.txt")
    print("Evaluation files created: validation metrics, predictions, residuals, importance, chart, and comparison report")
    print("Data leakage check: PASSED")


if __name__ == "__main__":
    main()