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
# SIH26170 — Module B V2
# Better early-behaviour features -> 168h prediction
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "module_b_prediction_features.csv"
)

MODEL_DIR = PROJECT_ROOT / "models"
REPORT_DIR = PROJECT_ROOT / "reports" / "prediction"

MODEL_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

REPORT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ------------------------------------------------------------
# Inputs available by 24h
# ------------------------------------------------------------

NUMERIC_FEATURES = [
    "ambient_temp_C",
    "burn_in_temp_C",
    "humidity_pct",

    "leakage_0h_uA",
    "leakage_24h_uA",

    "propagation_delay_0h_ns",
    "propagation_delay_24h_ns",

    "leakage_delta_0_24",
    "delay_delta_0_24",

    "leakage_relative_change_0_24",
    "delay_relative_change_0_24",

    "leakage_early_slope_uA_per_hour",
    "delay_early_slope_ns_per_hour",

    "leakage_peer_z_0h",
    "leakage_peer_z_24h",

    "delay_peer_z_0h",
    "delay_peer_z_24h",

    "leakage_peer_z_change",
    "delay_peer_z_change",

    "leakage_limit_margin_24h_uA",
    "delay_limit_margin_24h_ns",

    "leakage_limit_utilization_24h",
    "delay_limit_utilization_24h",

    "leakage_change_to_baseline_ratio",
    "delay_change_to_baseline_ratio",

    "max_abs_peer_z",
    "max_abs_change_z",
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
# Unseen test batches
# ------------------------------------------------------------

TEST_BATCHES = {
    "B09",
    "B10",
    "B11",
    "B20",
}


# ------------------------------------------------------------
# Load
# ------------------------------------------------------------

def load_data():

    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Prediction feature file not found:\n{DATA_FILE}"
        )

    df = pd.read_csv(
        DATA_FILE
    )

    required = (
        FEATURES
        + TARGETS
        + [
            "component_id",
            "batch_id",
        ]
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

    # Supervised regression requires known 168h targets.
    # Missing input features can be handled by the imputer,
    # but a missing target cannot be used for training.
    before = len(df)

    df = df.dropna(
        subset=TARGETS
    ).copy()

    removed = before - len(df)

    print(
        f"Removed {removed:,} rows with missing 168h targets."
    )

    print(
        f"Usable Module B rows: {len(df):,}"
    )

    return df

# ------------------------------------------------------------
# Leakage validation
# ------------------------------------------------------------

def validate_inputs():

    forbidden_input_columns = [
        "leakage_96h_uA",
        "leakage_168h_uA",
        "propagation_delay_96h_ns",
        "propagation_delay_168h_ns",
        "ground_truth_status",
        "behavior_type",
        "static_screen_fail",
    ]

    bad = [
        column
        for column in FEATURES
        if column in forbidden_input_columns
    ]

    if bad:
        raise AssertionError(
            "Forbidden information found in Module B inputs:\n"
            + "\n".join(bad)
        )

    print(
        "✓ Inputs contain only information available by 24h"
    )

    print(
        "✓ 168h measurements are targets only"
    )

    print(
        "✓ No evaluation labels are used as inputs"
    )


# ------------------------------------------------------------
# Train / test split
# ------------------------------------------------------------

def split_by_batch(df):

    train = df[
        ~df["batch_id"].isin(TEST_BATCHES)
    ].copy()

    test = df[
        df["batch_id"].isin(TEST_BATCHES)
    ].copy()

    if train.empty or test.empty:
        raise ValueError(
            "Invalid grouped split."
        )

    return train, test


# ------------------------------------------------------------
# Preprocessor
# ------------------------------------------------------------

def build_preprocessor():

    numeric = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(
                    strategy="median"
                ),
            ),
            (
                "scaler",
                StandardScaler()
            ),
        ]
    )

    categorical = Pipeline(
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
                numeric,
                NUMERIC_FEATURES,
            ),
            (
                "categorical",
                categorical,
                CATEGORICAL_FEATURES,
            ),
        ]
    )


# ------------------------------------------------------------
# Models
# ------------------------------------------------------------

def build_models():

    return {

        "Ridge": Ridge(
            alpha=1.0
        ),

        "RandomForest": RandomForestRegressor(
            n_estimators=500,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1,
        ),

        "HistGradientBoosting": MultiOutputRegressor(
            HistGradientBoostingRegressor(
                max_iter=350,
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

    leakage_true = y_true[:, 0]
    leakage_pred = y_pred[:, 0]

    delay_true = y_true[:, 1]
    delay_pred = y_pred[:, 1]

    return {
        "leakage_mae": mean_absolute_error(
            leakage_true,
            leakage_pred,
        ),

        "leakage_rmse": np.sqrt(
            mean_squared_error(
                leakage_true,
                leakage_pred,
            )
        ),

        "leakage_r2": r2_score(
            leakage_true,
            leakage_pred,
        ),

        "delay_mae": mean_absolute_error(
            delay_true,
            delay_pred,
        ),

        "delay_rmse": np.sqrt(
            mean_squared_error(
                delay_true,
                delay_pred,
            )
        ),

        "delay_r2": r2_score(
            delay_true,
            delay_pred,
        ),
    }


# ------------------------------------------------------------
# Normalized selection score
# ------------------------------------------------------------
#
# Leakage and delay have different physical units.
#
# We therefore normalize each MAE by the standard deviation
# of its training target before combining them.
#
# Lower = better.
# ------------------------------------------------------------

def normalized_selection_score(
    y_train,
    metrics,
):

    leakage_std = np.std(
        y_train[:, 0]
    )

    delay_std = np.std(
        y_train[:, 1]
    )

    leakage_component = (
        metrics["leakage_mae"]
        / leakage_std
    )

    delay_component = (
        metrics["delay_mae"]
        / delay_std
    )

    return (
        leakage_component
        + delay_component
    ) / 2.0


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main():

    validate_inputs()

    df = load_data()

    train, test = split_by_batch(
        df
    )

    print("\n" + "=" * 60)
    print("MODULE B V2 — DATA SPLIT")
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


    results = []
    fitted_models = {}
    predictions = {}


    # --------------------------------------------------------
    # Train all candidates
    # --------------------------------------------------------

    for name, model in build_models().items():

        print(
            f"\nTraining {name}..."
        )

        pipeline = Pipeline(
            steps=[
                (
                    "preprocessor",
                    build_preprocessor(),
                ),
                (
                    "model",
                    model,
                ),
            ]
        )

        try:

            pipeline.fit(
                X_train,
                y_train,
            )

            y_pred = pipeline.predict(
                X_test
            )

            metrics = calculate_metrics(
                y_test,
                y_pred,
            )

            metrics["model"] = name

            metrics["normalized_selection_score"] = (
                normalized_selection_score(
                    y_train,
                    metrics,
                )
            )

            results.append(
                metrics
            )

            fitted_models[name] = pipeline

            predictions[name] = y_pred

            print(
                f"  Leakage MAE : "
                f"{metrics['leakage_mae']:.4f} µA"
            )

            print(
                f"  Delay MAE   : "
                f"{metrics['delay_mae']:.4f} ns"
            )

            print(
                f"  Leakage R²  : "
                f"{metrics['leakage_r2']:.4f}"
            )

            print(
                f"  Delay R²    : "
                f"{metrics['delay_r2']:.4f}"
            )

        except Exception as exc:

            print(
                f"  {name} failed: {exc}"
            )


    if not results:

        raise RuntimeError(
            "Every Module B model failed."
        )


    # --------------------------------------------------------
    # Results table
    # --------------------------------------------------------

    results_df = pd.DataFrame(
        results
    )

    results_df = results_df.sort_values(
        "normalized_selection_score"
    )


    print("\n" + "=" * 60)
    print("MODULE B V2 BENCHMARK")
    print("=" * 60)

    print(
        results_df[
            [
                "model",
                "leakage_mae",
                "delay_mae",
                "leakage_r2",
                "delay_r2",
                "normalized_selection_score",
            ]
        ]
        .round(4)
        .to_string(index=False)
    )


    # --------------------------------------------------------
    # Select best model
    # --------------------------------------------------------

    best = results_df.iloc[0]

    best_name = best["model"]

    best_model = fitted_models[
        best_name
    ]

    best_predictions = predictions[
        best_name
    ]


    print(
        f"\nBest V2 model: {best_name}"
    )

    print(
        f"Leakage MAE : "
        f"{best['leakage_mae']:.4f} µA"
    )

    print(
        f"Delay MAE   : "
        f"{best['delay_mae']:.4f} ns"
    )


    # --------------------------------------------------------
    # Save predictions
    # --------------------------------------------------------

    prediction_output = test[
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

    prediction_output[
        "predicted_leakage_168h_uA"
    ] = best_predictions[:, 0]

    prediction_output[
        "predicted_delay_168h_ns"
    ] = best_predictions[:, 1]

    prediction_output[
        "predicted_leakage_slope_uA_per_hour"
    ] = (
        prediction_output[
            "predicted_leakage_168h_uA"
        ]
        - prediction_output[
            "leakage_24h_uA"
        ]
    ) / 144.0

    prediction_output[
        "predicted_delay_slope_ns_per_hour"
    ] = (
        prediction_output[
            "predicted_delay_168h_ns"
        ]
        - prediction_output[
            "propagation_delay_24h_ns"
        ]
    ) / 144.0

    prediction_output[
        "leakage_prediction_error_uA"
    ] = (
        prediction_output[
            "predicted_leakage_168h_uA"
        ]
        - prediction_output[
            "leakage_168h_uA"
        ]
    )

    prediction_output[
        "delay_prediction_error_ns"
    ] = (
        prediction_output[
            "predicted_delay_168h_ns"
        ]
        - prediction_output[
            "propagation_delay_168h_ns"
        ]
    )


    # --------------------------------------------------------
    # Save artifacts
    # --------------------------------------------------------

    benchmark_file = (
        REPORT_DIR
        / "module_b_v2_benchmark.csv"
    )

    prediction_file = (
        REPORT_DIR
        / "module_b_v2_predictions.csv"
    )

    model_file = (
        MODEL_DIR
        / "module_b_final_model.joblib"
    )

    metadata_file = (
        MODEL_DIR
        / "module_b_final_metadata.json"
    )


    results_df.to_csv(
        benchmark_file,
        index=False,
    )

    prediction_output.to_csv(
        prediction_file,
        index=False,
    )

    joblib.dump(
        best_model,
        model_file,
    )


    metadata = {
        "model": best_name,
        "features": FEATURES,
        "targets": TARGETS,
        "training_batches": sorted(
            train["batch_id"].unique()
        ),
        "test_batches": sorted(
            test["batch_id"].unique()
        ),
        "last_observed_hour": 24,
        "prediction_horizon_hour": 168,
        "forecast_window_hours": 144,
        "leakage_protected": True,
        "selection_metric": (
            "mean normalized MAE "
            "across leakage and delay"
        ),
    }

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
        "\nModule B V2 completed successfully."
    )


if __name__ == "__main__":
    main()
