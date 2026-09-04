"""Prepare chronological, leakage-safe train/validation/test data."""

from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


PROJECT_ROOT = Path(__file__).resolve().parents[2]
INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "gold_feature_dataset.csv"
MODEL_DATA_DIR = PROJECT_ROOT / "data" / "processed" / "model_data"
REPORT_PATH = PROJECT_ROOT / "reports" / "training_data_split_report.txt"
TARGET = "target_gold_999"
EXCLUDED_COLUMNS = ["date", TARGET, "gold_999_am", "gold_999_pm", "gold_999_avg", "source"]


def load_data() -> pd.DataFrame:
    """Load and validate the feature data in chronological order."""
    data = pd.read_csv(INPUT_PATH)
    data["date"] = pd.to_datetime(data["date"], errors="raise")
    data = data.sort_values("date").reset_index(drop=True)
    if data["date"].duplicated().any():
        raise ValueError("Duplicate dates found in feature dataset.")
    if data[TARGET].isna().any():
        raise ValueError("Missing target values found in feature dataset.")
    return data


def split_data(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split by row order, retaining earliest, middle, and latest observations."""
    train_end = int(len(data) * 0.70)
    validation_end = train_end + int(len(data) * 0.15)
    return data.iloc[:train_end].copy(), data.iloc[train_end:validation_end].copy(), data.iloc[validation_end:].copy()


def build_preprocessor(numeric_features: list[str], categorical_features: list[str]) -> ColumnTransformer:
    """Build preprocessing branches that will be fitted only on training data."""
    transformers = [
        (
            "numeric",
            Pipeline([( "imputer", SimpleImputer(strategy="median"))]),
            numeric_features,
        )
    ]
    if categorical_features:
        transformers.append(
            (
                "categorical",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
                    ]
                ),
                categorical_features,
            )
        )
    return ColumnTransformer(transformers=transformers, remainder="drop", verbose_feature_names_out=False)


def date_range(data: pd.DataFrame) -> str:
    """Return an ISO date range for a split."""
    return f"{data['date'].min().strftime('%Y-%m-%d')} to {data['date'].max().strftime('%Y-%m-%d')}"


def main() -> None:
    data = load_data()
    train, validation, test = split_data(data)
    feature_columns = [column for column in data.columns if column not in EXCLUDED_COLUMNS]
    numeric_features = data[feature_columns].select_dtypes(include="number").columns.tolist()
    categorical_features = data[feature_columns].select_dtypes(include=["object", "category", "bool"]).columns.tolist()

    X_train = train[feature_columns]
    X_validation = validation[feature_columns]
    X_test = test[feature_columns]
    y_train = train[[TARGET]]
    y_validation = validation[[TARGET]]
    y_test = test[[TARGET]]

    # Fit only on X_train; validation and test are transformed with that fitted object.
    preprocessor = build_preprocessor(numeric_features, categorical_features)
    X_train_processed = pd.DataFrame(preprocessor.fit_transform(X_train), columns=preprocessor.get_feature_names_out(), index=train.index)
    X_validation_processed = pd.DataFrame(preprocessor.transform(X_validation), columns=preprocessor.get_feature_names_out(), index=validation.index)
    X_test_processed = pd.DataFrame(preprocessor.transform(X_test), columns=preprocessor.get_feature_names_out(), index=test.index)

    MODEL_DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    for name, frame in {
        "X_train": X_train_processed,
        "X_validation": X_validation_processed,
        "X_test": X_test_processed,
        "y_train": y_train,
        "y_validation": y_validation,
        "y_test": y_test,
    }.items():
        frame.to_csv(MODEL_DATA_DIR / f"{name}.csv", index=False)
    for name, frame in {"train_dates": train, "validation_dates": validation, "test_dates": test}.items():
        frame[["date"]].assign(date=frame["date"].dt.strftime("%Y-%m-%d")).to_csv(MODEL_DATA_DIR / f"{name}.csv", index=False)
    joblib.dump(preprocessor, MODEL_DATA_DIR / "preprocessor.joblib")

    missing_before = {
        "train": int(X_train.isna().sum().sum()),
        "validation": int(X_validation.isna().sum().sum()),
        "test": int(X_test.isna().sum().sum()),
    }
    chronological = train["date"].max() < validation["date"].min() and validation["date"].max() < test["date"].min()
    if not chronological:
        raise RuntimeError("Chronological ordering validation failed.")

    report = "\n".join(
        [
            "TRAINING DATA SPLIT REPORT",
            "===========================",
            "",
            "1. DATASET INFORMATION",
            f"Input: {INPUT_PATH.relative_to(PROJECT_ROOT)}",
            f"Rows: {len(data)}",
            f"Columns: {len(data.columns)}",
            "",
            "2. TARGET DEFINITION",
            f"Target: {TARGET}",
            "Target values were not imputed or transformed.",
            "",
            "3. EXCLUDED COLUMNS",
            *[f"{column} (excluded when present)" for column in EXCLUDED_COLUMNS],
            "",
            "4. TRAIN/VALIDATION/TEST SIZES",
            f"Train rows: {len(train)}",
            f"Validation rows: {len(validation)}",
            f"Test rows: {len(test)}",
            f"Train date range: {date_range(train)}",
            f"Validation date range: {date_range(validation)}",
            f"Test date range: {date_range(test)}",
            "",
            "5. FEATURE TYPES",
            f"Numeric features ({len(numeric_features)}): {', '.join(numeric_features)}",
            f"Boolean features ({len(data[feature_columns].select_dtypes(include='bool').columns)}): {', '.join(data[feature_columns].select_dtypes(include='bool').columns)}",
            f"Categorical features ({len(categorical_features)}): {', '.join(categorical_features) if categorical_features else 'None'}",
            "",
            "6. FEATURE COUNT",
            f"Predictor features before preprocessing: {len(feature_columns)}",
            f"Features after preprocessing: {len(preprocessor.get_feature_names_out())}",
            "",
            "7. MISSING-VALUE HANDLING",
            f"Training missing values before preprocessing: {missing_before['train']}",
            f"Validation missing values before preprocessing: {missing_before['validation']}",
            f"Test missing values before preprocessing: {missing_before['test']}",
            "Numeric missing values use a median imputer fitted on X_train only.",
            "Categorical missing values use most-frequent imputation if categorical features exist.",
            "No target values were imputed.",
            "",
            "8. PREPROCESSING STRATEGY",
            "Numeric: SimpleImputer(strategy='median'); no scaling applied.",
            "Categorical: SimpleImputer(strategy='most_frequent') and OneHotEncoder(handle_unknown='ignore') when present.",
            "Preprocessed X files contain the train-fitted transformed values for tree-model readiness.",
            "",
            "9. LEAKAGE PREVENTION CHECKS",
            "Random shuffling: not used.",
            "Preprocessor fit: TRAINING DATA ONLY.",
            f"Chronological ordering: {'PASSED' if chronological else 'FAILED'}",
            "Excluded same-day IBJA target-source columns: PASSED.",
            "Future target values in preprocessing: not used.",
            "",
        ]
    )
    REPORT_PATH.write_text(report, encoding="utf-8")

    print("TRAIN SET")
    print(f"Rows: {len(train)}")
    print(f"Date range: {date_range(train)}")
    print("\nVALIDATION SET")
    print(f"Rows: {len(validation)}")
    print(f"Date range: {date_range(validation)}")
    print("\nTEST SET")
    print(f"Rows: {len(test)}")
    print(f"Date range: {date_range(test)}")
    print(f"\nNumeric features ({len(numeric_features)}): {numeric_features}")
    print(f"Boolean features: {data[feature_columns].select_dtypes(include='bool').columns.tolist()}")
    print(f"Categorical features ({len(categorical_features)}): {categorical_features or 'None'}")
    print("\nMissing values before preprocessing:")
    print(f"Training: {missing_before['train']}")
    print(f"Validation: {missing_before['validation']}")
    print(f"Test: {missing_before['test']}")
    print("\nTRAINING DATA PREPARATION COMPLETE")
    print(f"Dataset: {INPUT_PATH.relative_to(PROJECT_ROOT)}")
    print(f"Rows: {len(data)}")
    print(f"Features: {len(feature_columns)}")
    print(f"Train rows: {len(train)}")
    print(f"Validation rows: {len(validation)}")
    print(f"Test rows: {len(test)}")
    print(f"Train date range: {date_range(train)}")
    print(f"Validation date range: {date_range(validation)}")
    print(f"Test date range: {date_range(test)}")
    print(f"Feature count: {len(preprocessor.get_feature_names_out())}")
    print("Preprocessor fitted on: TRAINING DATA ONLY")
    print("Chronological ordering: PASSED")
    print("Data leakage check: PASSED")


if __name__ == "__main__":
    main()