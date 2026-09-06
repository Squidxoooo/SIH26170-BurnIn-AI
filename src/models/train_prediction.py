from pathlib import Path
import json

import numpy as np
import pandas as pd
import joblib

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import (
    RandomForestRegressor,
    HistGradientBoostingRegressor,
)
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.multioutput import MultiOutputRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


# ============================================================
# SIH26170 — Module B
# Early measurements → 168h prediction
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "module_b_regression.csv"
)

MODEL_DIR = PROJECT_ROOT / "models"
REPORT_DIR = PROJECT_ROOT / "reports" / "prediction"

MODEL_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# Prediction inputs
# ------------------------------------------------------------
#
# ONLY information available by 24h.
#
# batch_id and component_id are identifiers, not predictive
# features.
#
# 168h measurements are targets only.
# ------------------------------------------------------------

NUMERIC_FEATURES = [
    "ambient_temp_C",
    "burn_in_temp_C",
    "humidity_pct",

    "leakage_0h_uA",
    "leakage_24h_uA",

    "propagation_delay_0h_ns",
    "propagation_delay_24h_ns",
]

CATEGORICAL_FEATURES = [
    "device_family",
    "chamber_id",
]

FEATURES = (
    NUMERIC_FEATURES
    + CATEGORICAL_FEATURES
)

TARGETS = [
    "leakage_168h_uA",
    "propagation_delay_168h_ns",
]


# ------------------------------------------------------------
# Test batches
# ------------------------------------------------------------

TEST_BATCHES = {
    "B09",
    "B10",
    "B11",
    "B20",
}


# ------------------------------------------------------------
# Load dataset
# ------------------------------------------------------------

def load_data():

    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Module B dataset not found:\n{DATA_FILE}"
        )

    df = pd.read_csv(DATA_FILE)

    required = (
        FEATURES
        + TARGETS
        + ["batch_id", "split"]
    )

    missing = sorted(
        set(required) - set(df.columns)
    )

    if missing:
        raise ValueError(
            "Missing required columns:\n"
            + "\n".join(
                f"  - {column}"
                for column in missing
            )
        )

    # Make sure supervised targets exist.
    df = df.dropna(
        subset=TARGETS
    ).copy()

    return df


# ------------------------------------------------------------
# Leakage validation
# ------------------------------------------------------------

def validate_no_future_leakage():

    forbidden = [
        "leakage_96h_uA",
        "leakage_168h_uA",
        "propagation_delay_96h_ns",
        "propagation_delay_168h_ns",
        "behavior_type",
        "ground_truth_status",
        "static_screen_fail",
    ]

    bad = [
        column
        for column in FEATURES
        if column in forbidden
    ]

    if bad:
        raise AssertionError(
            "Future/evaluation information detected "
            "in Module B inputs:\n"
            + "\n".join(bad)
        )

    print(
        "✓ Module B inputs contain no 96h/168h measurements"
    )

    print(
        "✓ Module B inputs contain no evaluation labels"
    )


# ------------------------------------------------------------
# Split by batch
# ------------------------------------------------------------

def create_split(df):

    train = df[
        ~df["batch_id"].isin(TEST_BATCHES)
    ].copy()

    test = df[
        df["batch_id"].isin(TEST_BATCHES)
    ].copy()

    if train.empty or test.empty:
        raise ValueError(
            "Train/test split produced an empty dataset."
        )

    return train, test


# ------------------------------------------------------------
# Preprocessing
# ------------------------------------------------------------

def build_preprocessor():

    numeric_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(
                    strategy="median"
                ),
            ),
            (
                "scaler",
                StandardScaler(),
            ),
        ]
    )

    categorical_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(
                    strategy="most_frequent"
                ),
            ),
            (
                "onehot",
                OneHotEncoder(
                    handle_unknown="ignore",
                    sparse_output=False,
                ),
            ),
        ]
    )

    return ColumnTransformer(
        transformers=[
            (
                "numeric",
                numeric_pipeline,
                NUMERIC_FEATURES,
            ),
            (
                "categorical",
                categorical_pipeline,
                CATEGORICAL_FEATURES,
            ),
        ]
    )


# ------------------------------------------------------------
# Candidate models
# ------------------------------------------------------------

def build_models():

    return {
        "Ridge": Ridge(
            alpha=1.0
        ),

        "RandomForest": RandomForestRegressor(
            n_estimators=400,
            max_depth=None,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1,
        ),

        "HistGradientBoosting": MultiOutputRegressor(
            HistGradientBoostingRegressor(
                max_iter=300,
                learning_rate=0.05,
                max_leaf_nodes=31,
                l2_regularization=1.0,
                random_state=42,
            )
        ),
    }


# ------------------------------------------------------------
# Metrics
# ------------------------------------------------------------

def calculate_metrics(
    y_true,
    y_pred,
):

    metrics = {
        "overall_mae": mean_absolute_error(
            y_true,
            y_pred,
        ),

        "overall_rmse": np.sqrt(
            mean_squared_error(
                y_true,
                y_pred,
            )
        ),

        "overall_r2": r2_score(
            y_true,
            y_pred,
            multioutput="uniform_average",
        ),
    }

    # Leakage target metrics.
    metrics["leakage_mae"] = mean_absolute_error(
        y_true[:, 0],
        y_pred[:, 0],
    )

    metrics["leakage_rmse"] = np.sqrt(
        mean_squared_error(
            y_true[:, 0],
            y_pred[:, 0],
        )
    )

    metrics["leakage_r2"] = r2_score(
        y_true[:, 0],
        y_pred[:, 0],
    )

    # Delay target metrics.
    metrics["delay_mae"] = mean_absolute_error(
        y_true[:, 1],
        y_pred[:, 1],
    )

    metrics["delay_rmse"] = np.sqrt(
        mean_squared_error(
            y_true[:, 1],
            y_pred[:, 1],
        )
    )

    metrics["delay_r2"] = r2_score(
        y_true[:, 1],
        y_pred[:, 1],
    )

    return metrics


# ------------------------------------------------------------
# Evaluate model
# ------------------------------------------------------------

def evaluate_model(
    name,
    estimator,
    X_train,
    y_train,
    X_test,
    y_test,
):

    print(
        f"\nTraining {name}..."
    )

    estimator.fit(
        X_train,
        y_train,
    )

    y_pred = estimator.predict(
        X_test
    )

    metrics = calculate_metrics(
        y_test,
        y_pred,
    )

    metrics["model"] = name

    print(
        f"  Leakage MAE : "
        f"{metrics['leakage_mae']:.4f} µA"
    )

    print(
        f"  Delay MAE   : "
        f"{metrics['delay_mae']:.4f} ns"
    )

    print(
        f"  Overall MAE : "
        f"{metrics['overall_mae']:.4f}"
    )

    print(
        f"  Overall RMSE: "
        f"{metrics['overall_rmse']:.4f}"
    )

    print(
        f"  Overall R²  : "
        f"{metrics['overall_r2']:.4f}"
    )

    return estimator, metrics, y_pred


# ------------------------------------------------------------
# Calculate projected drift
# ------------------------------------------------------------

def add_prediction_columns(
    test,
    y_pred,
):

    result = test[
        [
            "component_id",
            "batch_id",
            "device_family",
            "chamber_id",
            "leakage_0h_uA",
            "leakage_24h_uA",
            "propagation_delay_0h_ns",
            "propagation_delay_24h_ns",
            "leakage_168h_uA",
            "propagation_delay_168h_ns",
        ]
    ].copy()

    result["predicted_leakage_168h_uA"] = (
        y_pred[:, 0]
    )

    result["predicted_delay_168h_ns"] = (
        y_pred[:, 1]
    )

    # From 24h → 168h there are 144 hours.
    forecast_hours = 168.0 - 24.0

    result["predicted_leakage_slope_uA_per_hour"] = (
        result["predicted_leakage_168h_uA"]
        - result["leakage_24h_uA"]
    ) / forecast_hours

    result["predicted_delay_slope_ns_per_hour"] = (
        result["predicted_delay_168h_ns"]
        - result["propagation_delay_24h_ns"]
    ) / forecast_hours

    # Prediction errors.
    result["leakage_prediction_error_uA"] = (
        result["predicted_leakage_168h_uA"]
        - result["leakage_168h_uA"]
    )

    result["delay_prediction_error_ns"] = (
        result["predicted_delay_168h_ns"]
        - result["propagation_delay_168h_ns"]
    )

    return result


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main():

    validate_no_future_leakage()

    df = load_data()

    train, test = create_split(
        df
    )

    print("\n" + "=" * 60)
    print("MODULE B — DATA SPLIT")
    print("=" * 60)

    print(
        f"Training components : "
        f"{len(train):,}"
    )

    print(
        f"Testing components  : "
        f"{len(test):,}"
    )

    print(
        f"Training batches    : "
        f"{train['batch_id'].nunique()}"
    )

    print(
        f"Testing batches     : "
        f"{test['batch_id'].nunique()}"
    )

    print(
        f"Test batches        : "
        f"{sorted(test['batch_id'].unique())}"
    )

    X_train = train[FEATURES]
    y_train = train[TARGETS].to_numpy()

    X_test = test[FEATURES]
    y_test = test[TARGETS].to_numpy()

    # --------------------------------------------------------
    # Benchmark
    # --------------------------------------------------------

    all_metrics = []
    fitted_models = {}
    predictions = {}

    for name, base_model in build_models().items():

        preprocessor = build_preprocessor()

        pipeline = Pipeline(
            steps=[
                (
                    "preprocessor",
                    preprocessor,
                ),
                (
                    "model",
                    base_model,
                ),
            ]
        )

        try:

            fitted, metrics, y_pred = evaluate_model(
                name,
                pipeline,
                X_train,
                y_train,
                X_test,
                y_test,
            )

            all_metrics.append(metrics)

            fitted_models[name] = fitted

            predictions[name] = y_pred

        except Exception as exc:

            print(
                f"\n{name} failed: {exc}"
            )

    if not all_metrics:
        raise RuntimeError(
            "All Module B models failed."
        )

    metrics_df = pd.DataFrame(
        all_metrics
    )

    # --------------------------------------------------------
    # Select best model
    # --------------------------------------------------------
    #
    # MAE is the primary SIH-style prediction metric.
    # We use normalized combined target performance by
    # selecting the lowest overall MAE.
    # --------------------------------------------------------

    best_row = metrics_df.sort_values(
        "overall_mae"
    ).iloc[0]

    best_name = best_row["model"]

    best_model = fitted_models[
        best_name
    ]

    best_prediction = predictions[
        best_name
    ]

    print("\n" + "=" * 60)
    print("MODULE B BENCHMARK SUMMARY")
    print("=" * 60)

    print(
        metrics_df[
            [
                "model",
                "leakage_mae",
                "leakage_rmse",
                "leakage_r2",
                "delay_mae",
                "delay_rmse",
                "delay_r2",
                "overall_mae",
                "overall_rmse",
                "overall_r2",
            ]
        ]
        .round(4)
        .to_string(index=False)
    )

    print(
        f"\nBest model by overall MAE: "
        f"{best_name}"
    )

    # --------------------------------------------------------
    # Save benchmark
    # --------------------------------------------------------

    benchmark_file = (
        REPORT_DIR
        / "module_b_model_benchmark.csv"
    )

    metrics_df.to_csv(
        benchmark_file,
        index=False,
    )

    # --------------------------------------------------------
    # Save predictions
    # --------------------------------------------------------

    prediction_df = add_prediction_columns(
        test,
        best_prediction,
    )

    prediction_file = (
        REPORT_DIR
        / "module_b_test_predictions.csv"
    )

    prediction_df.to_csv(
        prediction_file,
        index=False,
    )

    # --------------------------------------------------------
    # Save best model
    # --------------------------------------------------------

    model_file = (
        MODEL_DIR
        / "module_b_best_model.joblib"
    )

    joblib.dump(
        best_model,
        model_file,
    )

    metadata = {
        "model": best_name,
        "features": FEATURES,
        "targets": TARGETS,
        "test_batches": sorted(
            TEST_BATCHES
        ),
        "prediction_horizon_hours": 168,
        "last_observed_hour": 24,
        "forecast_window_hours": 144,
        "primary_metric": "overall_mae",
        "leakage_protected": True,
    }

    metadata_file = (
        MODEL_DIR
        / "module_b_metadata.json"
    )

    metadata_file.write_text(
        json.dumps(
            metadata,
            indent=2,
        )
    )

    print("\nSaved:")

    print(
        f"  {benchmark_file.relative_to(PROJECT_ROOT)}"
    )

    print(
        f"  {prediction_file.relative_to(PROJECT_ROOT)}"
    )

    print(
        f"  {model_file.relative_to(PROJECT_ROOT)}"
    )

    print(
        f"  {metadata_file.relative_to(PROJECT_ROOT)}"
    )

    print(
        "\nModule B training completed successfully."
    )


if __name__ == "__main__":
    main()
