from pathlib import Path
import json

import numpy as np
import pandas as pd
import joblib

from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.linear_model import Ridge
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.multioutput import MultiOutputRegressor


# ============================================================
# SIH26170 — Validation Predictions
#
# Purpose:
# Train models WITHOUT validation batches, then predict them.
#
# Final test batches remain completely untouched.
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

MODULE_A_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "module_a_ml_features.csv"
)

MODULE_B_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "module_b_prediction_features.csv"
)

LABEL_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "evaluation_labels.csv"
)

RAW_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "components_raw.csv"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "reports"
    / "risk"
)

MODEL_DIR = (
    PROJECT_ROOT
    / "models"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

MODEL_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ------------------------------------------------------------
# Evaluation design
# ------------------------------------------------------------

VALIDATION_BATCHES = {
    "B06",
    "B13",
    "B17",
}

FINAL_TEST_BATCHES = {
    "B09",
    "B10",
    "B11",
    "B20",
}


# ------------------------------------------------------------
# Module A features
# ------------------------------------------------------------

MODULE_A_FEATURES = [
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

    "leakage_change_to_baseline_ratio",
    "delay_change_to_baseline_ratio",

    "leakage_limit_margin_24h_uA",
    "delay_limit_margin_24h_ns",

    "leakage_limit_utilization_24h",
    "delay_limit_utilization_24h",

    "max_abs_peer_z",
    "max_abs_early_z",
    "max_abs_change_z",
]


# ------------------------------------------------------------
# Module B features
# ------------------------------------------------------------

MODULE_B_NUMERIC = [
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

MODULE_B_CATEGORICAL = [
    "device_family",
    "chamber_id",
]

MODULE_B_FEATURES = (
    MODULE_B_NUMERIC
    + MODULE_B_CATEGORICAL
)

TARGETS = [
    "leakage_168h_uA",
    "propagation_delay_168h_ns",
]


# ============================================================
# Load
# ============================================================

def load_data():

    module_a = pd.read_csv(
        MODULE_A_FILE
    )

    module_b = pd.read_csv(
        MODULE_B_FILE
    )

    labels = pd.read_csv(
        LABEL_FILE
    )

    raw = pd.read_csv(
        RAW_FILE
    )

    return (
        module_a,
        module_b,
        labels,
        raw,
    )


# ============================================================
# Module A
# ============================================================

def train_module_a(
    module_a,
):

    train = module_a[
        ~module_a["batch_id"].isin(
            VALIDATION_BATCHES
        )
        &
        ~module_a["batch_id"].isin(
            FINAL_TEST_BATCHES
        )
    ].copy()

    validation = module_a[
        module_a["batch_id"].isin(
            VALIDATION_BATCHES
        )
    ].copy()

    X_train = train[
        MODULE_A_FEATURES
    ]

    X_validation = validation[
        MODULE_A_FEATURES
    ]

    imputer = SimpleImputer(
        strategy="median"
    )

    scaler = StandardScaler()

    X_train = imputer.fit_transform(
        X_train
    )

    X_train = scaler.fit_transform(
        X_train
    )

    X_validation = imputer.transform(
        X_validation
    )

    X_validation = scaler.transform(
        X_validation
    )

    model = IsolationForest(
        n_estimators=400,
        contamination="auto",
        random_state=42,
        n_jobs=-1,
    )

    model.fit(
        X_train
    )

    train_raw = (
        -model.decision_function(
            X_train
        )
    )

    validation_raw = (
        -model.decision_function(
            X_validation
        )
    )

    # --------------------------------------------------------
    # Calibrate score from training distribution only.
    # --------------------------------------------------------

    sorted_train = np.sort(
        train_raw
    )

    ranks = np.searchsorted(
        sorted_train,
        validation_raw,
        side="right",
    )

    scores = ranks / len(
        sorted_train
    )

    scores = np.clip(
        scores,
        0.0,
        1.0,
    )

    result = validation[
        [
            "component_id",
            "batch_id",
        ]
    ].copy()

    result["anomaly_score"] = scores

    return result


# ============================================================
# Module B
# ============================================================

def train_module_b(
    module_b,
):

    # --------------------------------------------------------
    # Only rows with known targets can train regression.
    # --------------------------------------------------------

    module_b = module_b.dropna(
        subset=TARGETS
    ).copy()

    train = module_b[
        ~module_b["batch_id"].isin(
            VALIDATION_BATCHES
        )
        &
        ~module_b["batch_id"].isin(
            FINAL_TEST_BATCHES
        )
    ].copy()

    validation = module_b[
        module_b["batch_id"].isin(
            VALIDATION_BATCHES
        )
    ].copy()

    X_train = train[
        MODULE_B_FEATURES
    ]

    y_train = train[
        TARGETS
    ].to_numpy()

    X_validation = validation[
        MODULE_B_FEATURES
    ]

    # --------------------------------------------------------
    # Preprocessing
    # --------------------------------------------------------

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
                StandardScaler(),
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

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "numeric",
                numeric,
                MODULE_B_NUMERIC,
            ),
            (
                "categorical",
                categorical,
                MODULE_B_CATEGORICAL,
            ),
        ]
    )

    # --------------------------------------------------------
    # Use our selected V2 model: Ridge.
    # --------------------------------------------------------

    model = Pipeline(
        steps=[
            (
                "preprocessor",
                preprocessor,
            ),
            (
                "model",
                Ridge(
                    alpha=1.0
                ),
            ),
        ]
    )

    model.fit(
        X_train,
        y_train,
    )

    predictions = model.predict(
        X_validation
    )

    result = validation[
        [
            "component_id",
            "batch_id",
            "leakage_24h_uA",
            "propagation_delay_24h_ns",
        ]
    ].copy()

    result[
        "predicted_leakage_168h_uA"
    ] = predictions[:, 0]

    result[
        "predicted_delay_168h_ns"
    ] = predictions[:, 1]

    # --------------------------------------------------------
    # Projected 24h -> 168h slopes.
    # --------------------------------------------------------

    forecast_hours = 144.0

    result[
        "predicted_leakage_slope_uA_per_hour"
    ] = (
        result[
            "predicted_leakage_168h_uA"
        ]
        - result[
            "leakage_24h_uA"
        ]
    ) / forecast_hours

    result[
        "predicted_delay_slope_ns_per_hour"
    ] = (
        result[
            "predicted_delay_168h_ns"
        ]
        - result[
            "propagation_delay_24h_ns"
        ]
    ) / forecast_hours

    return result


# ============================================================
# Merge outputs
# ============================================================

def build_combined(
    anomaly,
    prediction,
    labels,
    raw,
):

    limits = raw[
        [
            "component_id",
            "batch_id",
            "device_family",
            "leakage_static_limit_uA",
            "delay_static_limit_ns",
        ]
    ].drop_duplicates(
        subset=["component_id"]
    )

    result = (
        anomaly
        .merge(
            prediction,
            on=[
                "component_id",
                "batch_id",
            ],
            how="inner",
        )
        .merge(
            limits,
            on=[
                "component_id",
                "batch_id",
            ],
            how="left",
        )
        .merge(
            labels[
                [
                    "component_id",
                    "batch_id",
                    "ground_truth_status",
                    "static_screen_fail",
                    "behavior_type",
                ]
            ],
            on=[
                "component_id",
                "batch_id",
            ],
            how="left",
        )
    )

    return result


# ============================================================
# Save
# ============================================================

def main():

    (
        module_a,
        module_b,
        labels,
        raw,
    ) = load_data()

    print("=" * 60)
    print("SIH26170 — VALIDATION PREDICTIONS")
    print("=" * 60)

    print(
        f"Validation batches: "
        f"{sorted(VALIDATION_BATCHES)}"
    )

    print(
        f"Final test batches: "
        f"{sorted(FINAL_TEST_BATCHES)}"
    )

    anomaly = train_module_a(
        module_a
    )

    print(
        f"\nModule A validation predictions: "
        f"{len(anomaly):,}"
    )

    prediction = train_module_b(
        module_b
    )

    print(
        f"Module B validation predictions: "
        f"{len(prediction):,}"
    )

    combined = build_combined(
        anomaly,
        prediction,
        labels,
        raw,
    )

    output_file = (
        OUTPUT_DIR
        / "validation_predictions.csv"
    )

    combined.to_csv(
        output_file,
        index=False,
    )

    print(
        f"\nSaved:"
    )

    print(
        f"  {output_file.relative_to(PROJECT_ROOT)}"
    )

    print(
        "\nValidation prediction generation completed."
    )


if __name__ == "__main__":
    main()
