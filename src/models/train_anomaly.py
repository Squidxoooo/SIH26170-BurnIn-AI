from pathlib import Path
import json

import numpy as np
import pandas as pd
import joblib

from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


# ============================================================
# SIH26170 — Module A: Isolation Forest
# Proper train-only score calibration
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

FEATURE_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "module_a_ml_features.csv"
)

LABEL_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "evaluation_labels.csv"
)

OUTPUT_DIR = PROJECT_ROOT / "models"
REPORT_DIR = PROJECT_ROOT / "reports" / "eda"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# Model features
# ------------------------------------------------------------

MODEL_FEATURES = [
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
# Load data
# ------------------------------------------------------------

def load_data():
    if not FEATURE_FILE.exists():
        raise FileNotFoundError(
            f"Feature file not found:\n{FEATURE_FILE}"
        )

    if not LABEL_FILE.exists():
        raise FileNotFoundError(
            f"Evaluation label file not found:\n{LABEL_FILE}"
        )

    features = pd.read_csv(FEATURE_FILE)
    labels = pd.read_csv(LABEL_FILE)

    missing = sorted(
        set(MODEL_FEATURES) - set(features.columns)
    )

    if missing:
        raise ValueError(
            "Missing model features:\n"
            + "\n".join(
                f"  - {column}"
                for column in missing
            )
        )

    print(
        f"Loaded features: "
        f"{len(features):,} components"
    )

    return features, labels


# ------------------------------------------------------------
# Input validation
# ------------------------------------------------------------

def validate_inputs():
    forbidden = [
        "ground_truth_status",
        "behavior_type",
        "static_screen_fail",
        "leakage_96h_uA",
        "leakage_168h_uA",
        "propagation_delay_96h_ns",
        "propagation_delay_168h_ns",
    ]

    bad = [
        column
        for column in MODEL_FEATURES
        if column in forbidden
    ]

    if bad:
        raise AssertionError(
            "Forbidden information detected:\n"
            + "\n".join(bad)
        )

    print(
        "✓ No ground-truth labels used as model inputs"
    )

    print(
        "✓ No 96h/168h measurements used as model inputs"
    )


# ------------------------------------------------------------
# Grouped train/test split
# ------------------------------------------------------------

def create_split(features):
    test_batches = {
        "B09",
        "B10",
        "B11",
        "B20",
    }

    train_mask = ~features["batch_id"].isin(test_batches)
    test_mask = features["batch_id"].isin(test_batches)

    train = features.loc[train_mask].copy()
    test = features.loc[test_mask].copy()

    return train, test


# ------------------------------------------------------------
# Build Isolation Forest
# ------------------------------------------------------------

def build_model():
    return Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(strategy="median"),
            ),
            (
                "scaler",
                StandardScaler(),
            ),
            (
                "isolation_forest",
                IsolationForest(
                    n_estimators=400,
                    contamination="auto",
                    random_state=42,
                    n_jobs=-1,
                ),
            ),
        ]
    )


# ------------------------------------------------------------
# TRAIN-ONLY score calibration
# ------------------------------------------------------------

def calibrate_score_range(model, train):
    train_raw = -model.decision_function(
        train[MODEL_FEATURES]
    )

    score_min = float(np.min(train_raw))
    score_max = float(np.max(train_raw))

    if score_max <= score_min:
        raise ValueError(
            "Training anomaly scores have no usable range."
        )

    return {
        "min": score_min,
        "max": score_max,
    }


def normalize_scores(raw_scores, calibration):
    minimum = calibration["min"]
    maximum = calibration["max"]

    scores = (
        (raw_scores - minimum)
        / (maximum - minimum)
    )

    return np.clip(scores, 0.0, 1.0)


# ------------------------------------------------------------
# Generate anomaly scores
# ------------------------------------------------------------

def score_dataset(model, df, calibration):
    X = df[MODEL_FEATURES]

    raw_score = -model.decision_function(X)

    anomaly_score = normalize_scores(
        raw_score,
        calibration,
    )

    result = df[
        [
            "component_id",
            "batch_id",
            "device_family",
            "chamber_id",
        ]
    ].copy()

    result["anomaly_score"] = anomaly_score
    result["raw_anomaly_score"] = raw_score

    result["isolation_prediction"] = (
        model.predict(X) == -1
    )

    return result


# ------------------------------------------------------------
# Evaluation
# ------------------------------------------------------------

def evaluate(scored, labels):
    result = scored.merge(
        labels[
            [
                "component_id",
                "batch_id",
                "behavior_type",
                "ground_truth_status",
                "static_screen_fail",
            ]
        ],
        on=["component_id", "batch_id"],
        how="left",
    )

    latent = (
        (result["ground_truth_status"] == "Defective")
        & (~result["static_screen_fail"].fillna(False))
    )

    healthy = (
        result["ground_truth_status"] == "Healthy"
    )

    print("\n" + "=" * 60)
    print("MODULE A — TEST EVALUATION")
    print("=" * 60)

    print(
        f"Test components : {len(result):,}"
    )

    print(
        f"Latent defects  : {latent.sum():,}"
    )

    print(
        f"Healthy         : {healthy.sum():,}"
    )

    thresholds = [
        0.20,
        0.30,
        0.40,
        0.50,
        0.60,
        0.70,
        0.80,
    ]

    for threshold in thresholds:
        flagged = (
            result["anomaly_score"] >= threshold
        )

        tp = (flagged & latent).sum()
        fn = ((~flagged) & latent).sum()
        fp = (flagged & healthy).sum()
        tn = ((~flagged) & healthy).sum()

        recall = (
            tp / (tp + fn)
            if (tp + fn)
            else 0.0
        )

        precision = (
            tp / (tp + fp)
            if (tp + fp)
            else 0.0
        )

        false_positive_rate = (
            fp / (fp + tn)
            if (fp + tn)
            else 0.0
        )

        print(f"\nThreshold {threshold:.2f}")
        print(f"  Flagged        : {flagged.sum():,}")
        print(f"  Recall         : {recall:.3f}")
        print(f"  Precision      : {precision:.3f}")
        print(
            f"  False positive : "
            f"{false_positive_rate:.3f}"
        )

    return result


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main():
    validate_inputs()

    features, labels = load_data()

    train, test = create_split(features)

    print("\nGrouped split:")

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

    # --------------------------------------------------------
    # Train model
    # --------------------------------------------------------

    print("\nTraining Isolation Forest...")

    model = build_model()

    model.fit(
        train[MODEL_FEATURES]
    )

    print(
        "✓ Model trained on training batches only"
    )

    # --------------------------------------------------------
    # Calibrate ONLY from training data
    # --------------------------------------------------------

    print(
        "\nCalibrating anomaly score "
        "using training data only..."
    )

    calibration = calibrate_score_range(
        model,
        train,
    )

    print(
        f"✓ Training score minimum: "
        f"{calibration['min']:.6f}"
    )

    print(
        f"✓ Training score maximum: "
        f"{calibration['max']:.6f}"
    )

    # --------------------------------------------------------
    # Score unseen test batches
    # --------------------------------------------------------

    print(
        "\nScoring unseen test batches..."
    )

    test_scores = score_dataset(
        model,
        test,
        calibration,
    )

    # --------------------------------------------------------
    # Evaluate
    # --------------------------------------------------------

    evaluation = evaluate(
        test_scores,
        labels,
    )

    # --------------------------------------------------------
    # Save predictions
    # --------------------------------------------------------

    prediction_file = (
        REPORT_DIR
        / "module_a_test_predictions.csv"
    )

    evaluation.to_csv(
        prediction_file,
        index=False,
    )

    # --------------------------------------------------------
    # Save model
    # --------------------------------------------------------

    model_file = (
        OUTPUT_DIR
        / "module_a_isolation_forest.joblib"
    )

    joblib.dump(
        model,
        model_file,
    )

    calibration_file = (
        OUTPUT_DIR
        / "module_a_score_calibration.json"
    )

    calibration_file.write_text(
        json.dumps(
            calibration,
            indent=2,
        )
    )

    print("\nSaved:")

    print(
        f"  {prediction_file.relative_to(PROJECT_ROOT)}"
    )

    print(
        f"  {model_file.relative_to(PROJECT_ROOT)}"
    )

    print(
        f"  {calibration_file.relative_to(PROJECT_ROOT)}"
    )

    print(
        "\nModule A completed successfully."
    )


if __name__ == "__main__":
    main()
