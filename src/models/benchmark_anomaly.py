from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.covariance import EllipticEnvelope
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler


# ============================================================
# SIH26170 — Module A Model Benchmark
# Unsupervised anomaly detection
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

REPORT_DIR = PROJECT_ROOT / "reports" / "eda"

REPORT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ------------------------------------------------------------
# Numeric model features
# ------------------------------------------------------------
#
# No IDs.
# No categorical strings.
# No labels.
# No 96h/168h information.
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
            f"Label file not found:\n{LABEL_FILE}"
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

    return features, labels


# ------------------------------------------------------------
# Train / test split
# ------------------------------------------------------------

def create_split(features):

    test_batches = {
        "B09",
        "B10",
        "B11",
        "B20",
    }

    train_mask = (
        ~features["batch_id"].isin(test_batches)
    )

    test_mask = (
        features["batch_id"].isin(test_batches)
    )

    train = features.loc[
        train_mask
    ].copy()

    test = features.loc[
        test_mask
    ].copy()

    return train, test


# ------------------------------------------------------------
# Preprocess using TRAINING data only
# ------------------------------------------------------------

def preprocess(train, test):

    imputer = SimpleImputer(
        strategy="median"
    )

    scaler = StandardScaler()

    X_train = imputer.fit_transform(
        train[MODEL_FEATURES]
    )

    X_train = scaler.fit_transform(
        X_train
    )

    X_test = imputer.transform(
        test[MODEL_FEATURES]
    )

    X_test = scaler.transform(
        X_test
    )

    return X_train, X_test


# ------------------------------------------------------------
# Convert raw model output into a 0–1 anomaly score
# using ONLY the training score distribution.
# ------------------------------------------------------------

def calibrate_scores(
    train_raw,
    test_raw,
):

    train_sorted = np.sort(
        train_raw
    )

    def percentile_score(values):

        ranks = np.searchsorted(
            train_sorted,
            values,
            side="right",
        )

        score = ranks / len(
            train_sorted
        )

        return np.clip(
            score,
            0.0,
            1.0,
        )

    return percentile_score(
        train_raw
    ), percentile_score(
        test_raw
    )


# ------------------------------------------------------------
# Evaluation
# ------------------------------------------------------------

def evaluate_model(
    name,
    train_raw,
    test_raw,
    test,
    labels,
):

    _, test_scores = calibrate_scores(
        train_raw,
        test_raw,
    )

    scored = test[
        [
            "component_id",
            "batch_id",
            "device_family",
            "chamber_id",
        ]
    ].copy()

    scored["anomaly_score"] = test_scores

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
        on=[
            "component_id",
            "batch_id",
        ],
        how="left",
    )

    latent = (
        (result["ground_truth_status"] == "Defective")
        &
        (~result["static_screen_fail"].fillna(False))
    )

    healthy = (
        result["ground_truth_status"] == "Healthy"
    )

    print("\n" + "=" * 60)
    print(f"{name}")
    print("=" * 60)

    print(
        f"Latent defects : {latent.sum():,}"
    )

    print(
        f"Healthy        : {healthy.sum():,}"
    )

    results = []

    for threshold in [
        0.90,
        0.95,
        0.97,
        0.98,
        0.99,
    ]:

        flagged = (
            result["anomaly_score"]
            >= threshold
        )

        tp = (
            flagged & latent
        ).sum()

        fn = (
            (~flagged) & latent
        ).sum()

        fp = (
            flagged & healthy
        ).sum()

        tn = (
            (~flagged) & healthy
        ).sum()

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

        fpr = (
            fp / (fp + tn)
            if (fp + tn)
            else 0.0
        )

        results.append({
            "model": name,
            "threshold": threshold,
            "flagged": int(flagged.sum()),
            "recall": recall,
            "precision": precision,
            "false_positive_rate": fpr,
        })

        print(
            f"\nThreshold {threshold:.2f}"
        )

        print(
            f"  Flagged        : {flagged.sum():,}"
        )

        print(
            f"  Recall         : {recall:.3f}"
        )

        print(
            f"  Precision      : {precision:.3f}"
        )

        print(
            f"  False positive : {fpr:.3f}"
        )

    return (
        result,
        pd.DataFrame(results),
    )


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main():

    features, labels = load_data()

    train, test = create_split(
        features
    )

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
    # Preprocessing
    # --------------------------------------------------------

    print(
        "\nPreprocessing using training data only..."
    )

    X_train, X_test = preprocess(
        train,
        test,
    )

    print(
        "✓ Missing-value imputation "
        "fit on training data only"
    )

    print(
        "✓ Feature scaling fit on "
        "training data only"
    )

    # --------------------------------------------------------
    # Model 1 — Isolation Forest
    # --------------------------------------------------------

    print(
        "\nTraining Isolation Forest..."
    )

    isolation_forest = IsolationForest(
        n_estimators=400,
        contamination="auto",
        random_state=42,
        n_jobs=-1,
    )

    isolation_forest.fit(
        X_train
    )

    train_if = (
        -isolation_forest
        .decision_function(X_train)
    )

    test_if = (
        -isolation_forest
        .decision_function(X_test)
    )

    if_result, if_metrics = evaluate_model(
        "Isolation Forest",
        train_if,
        test_if,
        test,
        labels,
    )

    # --------------------------------------------------------
    # Model 2 — Local Outlier Factor
    # --------------------------------------------------------

    print(
        "\nTraining Local Outlier Factor..."
    )

    lof = LocalOutlierFactor(
        n_neighbors=35,
        contamination="auto",
        novelty=True,
    )

    lof.fit(
        X_train
    )

    train_lof = (
        -lof.decision_function(X_train)
    )

    test_lof = (
        -lof.decision_function(X_test)
    )

    lof_result, lof_metrics = evaluate_model(
        "Local Outlier Factor",
        train_lof,
        test_lof,
        test,
        labels,
    )

    # --------------------------------------------------------
    # Model 3 — Elliptic Envelope
    # --------------------------------------------------------

    print(
        "\nTraining Elliptic Envelope..."
    )

    elliptic = EllipticEnvelope(
        contamination=0.05,
        random_state=42,
    )

    try:

        elliptic.fit(
            X_train
        )

        train_ee = (
            -elliptic.decision_function(
                X_train
            )
        )

        test_ee = (
            -elliptic.decision_function(
                X_test
            )
        )

        ee_result, ee_metrics = evaluate_model(
            "Elliptic Envelope",
            train_ee,
            test_ee,
            test,
            labels,
        )

    except Exception as exc:

        print(
            "\nElliptic Envelope failed:"
            f" {exc}"
        )

        ee_result = None
        ee_metrics = pd.DataFrame()


    # --------------------------------------------------------
    # Combine benchmark results
    # --------------------------------------------------------

    metrics = pd.concat(
        [
            if_metrics,
            lof_metrics,
            ee_metrics,
        ],
        ignore_index=True,
    )

    output_file = (
        REPORT_DIR
        / "module_a_model_benchmark.csv"
    )

    metrics.to_csv(
        output_file,
        index=False,
    )

    # --------------------------------------------------------
    # Print best candidates
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("MODULE A BENCHMARK SUMMARY")
    print("=" * 60)

    print(
        metrics[
            [
                "model",
                "threshold",
                "recall",
                "precision",
                "false_positive_rate",
            ]
        ]
        .round(3)
        .to_string(index=False)
    )

    # Best by recall under 5% false-positive rate.
    acceptable = metrics[
        metrics["false_positive_rate"] <= 0.05
    ].copy()

    if len(acceptable):

        best = acceptable.sort_values(
            [
                "recall",
                "precision",
            ],
            ascending=False,
        ).iloc[0]

        print(
            "\nBest candidate under "
            "5% false-positive rate:"
        )

        print(
            f"  Model      : {best['model']}"
        )

        print(
            f"  Threshold  : {best['threshold']:.2f}"
        )

        print(
            f"  Recall     : {best['recall']:.3f}"
        )

        print(
            f"  Precision  : {best['precision']:.3f}"
        )

        print(
            f"  False-positive: "
            f"{best['false_positive_rate']:.3f}"
        )

    else:

        print(
            "\nNo model/threshold achieved "
            "a false-positive rate <= 5%."
        )

    print(
        f"\nSaved benchmark to:\n"
        f"{output_file.relative_to(PROJECT_ROOT)}"
    )


if __name__ == "__main__":
    main()
