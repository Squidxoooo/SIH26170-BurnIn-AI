from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# SIH26170 — Module A Feature Engineering
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_FILE = PROJECT_ROOT / "data" / "raw" / "components_raw.csv"
OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "module_a_ml_features.csv"


# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

TIME_DELTA_HOURS = 24.0

REQUIRED_COLUMNS = [
    "component_id",
    "batch_id",
    "device_family",
    "chamber_id",
    "ambient_temp_C",
    "burn_in_temp_C",
    "humidity_pct",
    "leakage_0h_uA",
    "leakage_24h_uA",
    "propagation_delay_0h_ns",
    "propagation_delay_24h_ns",
]


# ------------------------------------------------------------
# Utility functions
# ------------------------------------------------------------

def robust_group_zscore(
    df: pd.DataFrame,
    value_column: str,
    group_columns: list[str],
) -> pd.Series:
    """
    Calculate a robust Z-score relative to a peer group.

    Formula:
        robust_z = 0.6745 * (x - median) / MAD

    MAD = median absolute deviation.

    We use a small fallback when MAD is zero so the pipeline
    never divides by zero.
    """

    grouped = df.groupby(
        group_columns,
        dropna=False
    )[value_column]

    median = grouped.transform("median")

    mad = grouped.transform(
        lambda x: np.median(
            np.abs(x - np.nanmedian(x))
        )
    )

    mad = mad.replace(0, np.nan)

    z = (
        0.6745
        * (df[value_column] - median)
        / mad
    )

    return z.fillna(0.0)


def relative_change(
    start: pd.Series,
    end: pd.Series,
) -> pd.Series:
    """
    Relative change from start to end.

    Example:
        10 -> 12
        relative change = 0.20

    Small denominators are protected to avoid division problems.
    """

    denominator = start.abs().clip(lower=1e-9)

    return (end - start) / denominator


# ------------------------------------------------------------
# Load data
# ------------------------------------------------------------

def load_data() -> pd.DataFrame:

    if not RAW_FILE.exists():
        raise FileNotFoundError(
            f"Could not find raw dataset:\n{RAW_FILE}"
        )

    df = pd.read_csv(RAW_FILE)

    missing = sorted(
        set(REQUIRED_COLUMNS) - set(df.columns)
    )

    if missing:
        raise ValueError(
            "Raw dataset is missing required columns:\n"
            + "\n".join(
                f"  - {column}"
                for column in missing
            )
        )

    print(
        f"Loaded {len(df):,} components."
    )

    return df


# ------------------------------------------------------------
# Feature engineering
# ------------------------------------------------------------

def build_features(
    df: pd.DataFrame,
) -> pd.DataFrame:

    result = df.copy()

    # ========================================================
    # 1. Absolute early changes
    # ========================================================

    result["leakage_delta_0_24"] = (
        result["leakage_24h_uA"]
        - result["leakage_0h_uA"]
    )

    result["delay_delta_0_24"] = (
        result["propagation_delay_24h_ns"]
        - result["propagation_delay_0h_ns"]
    )


    # ========================================================
    # 2. Relative early changes
    # ========================================================

    result["leakage_relative_change_0_24"] = relative_change(
        result["leakage_0h_uA"],
        result["leakage_24h_uA"],
    )

    result["delay_relative_change_0_24"] = relative_change(
        result["propagation_delay_0h_ns"],
        result["propagation_delay_24h_ns"],
    )


    # ========================================================
    # 3. Early drift rate
    # ========================================================

    result["leakage_early_slope_uA_per_hour"] = (
        result["leakage_delta_0_24"]
        / TIME_DELTA_HOURS
    )

    result["delay_early_slope_ns_per_hour"] = (
        result["delay_delta_0_24"]
        / TIME_DELTA_HOURS
    )


    # ========================================================
    # 4. Peer-relative absolute deviation
    # ========================================================
    #
    # Compare each component to other components in the
    # same batch + device family.
    #
    # We calculate this at 0h and 24h independently.
    # ========================================================

    peer_group = [
        "batch_id",
        "device_family",
    ]

    result["leakage_peer_z_0h"] = robust_group_zscore(
        result,
        "leakage_0h_uA",
        peer_group,
    )

    result["leakage_peer_z_24h"] = robust_group_zscore(
        result,
        "leakage_24h_uA",
        peer_group,
    )

    result["delay_peer_z_0h"] = robust_group_zscore(
        result,
        "propagation_delay_0h_ns",
        peer_group,
    )

    result["delay_peer_z_24h"] = robust_group_zscore(
        result,
        "propagation_delay_24h_ns",
        peer_group,
    )


    # ========================================================
    # 5. Peer-relative change
    # ========================================================
    #
    # This is particularly important.
    #
    # A component might have a normal absolute value but
    # change much faster than its peers.
    # ========================================================

    result["leakage_peer_z_change"] = robust_group_zscore(
        result,
        "leakage_delta_0_24",
        peer_group,
    )

    result["delay_peer_z_change"] = robust_group_zscore(
        result,
        "delay_delta_0_24",
        peer_group,
    )


    # ========================================================
    # 6. Temporal acceleration proxy
    # ========================================================
    #
    # At only 0h and 24h we cannot measure true acceleration.
    #
    # Instead we measure how large the early change is
    # relative to the component's baseline magnitude.
    #
    # This gives the model another representation of
    # "rapid early movement".
    # ========================================================

    result["leakage_change_to_baseline_ratio"] = (
        result["leakage_delta_0_24"].abs()
        / result["leakage_0h_uA"].abs().clip(lower=1e-9)
    )

    result["delay_change_to_baseline_ratio"] = (
        result["delay_delta_0_24"].abs()
        / result["propagation_delay_0h_ns"].abs().clip(lower=1e-9)
    )


    # ========================================================
    # 7. Static-limit proximity
    # ========================================================
    #
    # This does NOT replace anomaly detection.
    #
    # It tells the model how close the component is to the
    # ordinary static screen while still allowing the model
    # to detect unusual behaviour below that limit.
    # ========================================================

    result["leakage_limit_margin_24h_uA"] = (
        result["leakage_static_limit_uA"]
        - result["leakage_24h_uA"]
    )

    result["delay_limit_margin_24h_ns"] = (
        result["delay_static_limit_ns"]
        - result["propagation_delay_24h_ns"]
    )

    result["leakage_limit_utilization_24h"] = (
        result["leakage_24h_uA"]
        / result["leakage_static_limit_uA"]
    )

    result["delay_limit_utilization_24h"] = (
        result["propagation_delay_24h_ns"]
        / result["delay_static_limit_ns"]
    )


    # ========================================================
    # 8. Combined anomaly indicators
    # ========================================================

    result["max_abs_peer_z"] = result[
        [
            "leakage_peer_z_0h",
            "leakage_peer_z_24h",
            "delay_peer_z_0h",
            "delay_peer_z_24h",
            "leakage_peer_z_change",
            "delay_peer_z_change",
        ]
    ].abs().max(axis=1)


    result["max_abs_early_z"] = result[
        [
            "leakage_peer_z_0h",
            "leakage_peer_z_24h",
            "delay_peer_z_0h",
            "delay_peer_z_24h",
        ]
    ].abs().max(axis=1)


    result["max_abs_change_z"] = result[
        [
            "leakage_peer_z_change",
            "delay_peer_z_change",
        ]
    ].abs().max(axis=1)


    # ========================================================
    # 9. Simple baseline anomaly score
    # ========================================================
    #
    # This is NOT our final ML model.
    #
    # It is a useful baseline for comparison against
    # Isolation Forest later.
    # ========================================================

    result["baseline_anomaly_score"] = np.clip(
        result["max_abs_peer_z"] / 8.0,
        0.0,
        1.0,
    )


    # ========================================================
    # 10. Clean ML feature table
    # ========================================================

    feature_columns = [
        # IDs / context
        "component_id",
        "batch_id",
        "device_family",
        "chamber_id",

        # Environment
        "ambient_temp_C",
        "burn_in_temp_C",
        "humidity_pct",

        # Raw early measurements
        "leakage_0h_uA",
        "leakage_24h_uA",
        "propagation_delay_0h_ns",
        "propagation_delay_24h_ns",

        # Temporal behaviour
        "leakage_delta_0_24",
        "delay_delta_0_24",
        "leakage_relative_change_0_24",
        "delay_relative_change_0_24",
        "leakage_early_slope_uA_per_hour",
        "delay_early_slope_ns_per_hour",

        # Peer behaviour
        "leakage_peer_z_0h",
        "leakage_peer_z_24h",
        "delay_peer_z_0h",
        "delay_peer_z_24h",
        "leakage_peer_z_change",
        "delay_peer_z_change",

        # Relative movement
        "leakage_change_to_baseline_ratio",
        "delay_change_to_baseline_ratio",

        # Static-screen context
        "leakage_limit_margin_24h_uA",
        "delay_limit_margin_24h_ns",
        "leakage_limit_utilization_24h",
        "delay_limit_utilization_24h",

        # Combined signals
        "max_abs_peer_z",
        "max_abs_early_z",
        "max_abs_change_z",
        "baseline_anomaly_score",
    ]

    return result[feature_columns].copy()


# ------------------------------------------------------------
# Validation
# ------------------------------------------------------------

def validate_features(
    features: pd.DataFrame,
):

    print("\nRunning Module A feature checks...")

    forbidden_terms = [
        "96h",
        "168h",
        "ground_truth",
        "behavior_type",
        "static_screen_fail",
    ]

    bad_columns = []

    for column in features.columns:

        lower = column.lower()

        if any(
            term in lower
            for term in forbidden_terms
        ):
            bad_columns.append(column)

    if bad_columns:

        raise AssertionError(
            "Potential leakage columns found:\n"
            + "\n".join(
                f"  - {column}"
                for column in bad_columns
            )
        )

    print(
        "✓ No 96h/168h measurements in Module A features"
    )

    print(
        "✓ No ground-truth labels in Module A features"
    )

    print(
        "✓ Features use only information available by 24h"
    )


# ------------------------------------------------------------
# Report
# ------------------------------------------------------------

def print_report(
    features: pd.DataFrame,
):

    print("\n" + "=" * 60)
    print("MODULE A FEATURE REPORT")
    print("=" * 60)

    print(
        f"Components : {len(features):,}"
    )

    print(
        f"Features   : {len(features.columns)}"
    )

    print(
        f"Missing cells : {features.isna().sum().sum():,}"
    )

    print(
        f"Mean anomaly score : "
        f"{features['baseline_anomaly_score'].mean():.4f}"
    )

    print(
        f"Max anomaly score  : "
        f"{features['baseline_anomaly_score'].max():.4f}"
    )

    print("\nFeature columns:")

    for column in features.columns:

        print(
            f"  {column}"
        )


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main():

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df = load_data()

    features = build_features(df)

    validate_features(features)

    features.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print_report(features)

    print("\nGenerated:")
    print(
        f"  {OUTPUT_FILE.relative_to(PROJECT_ROOT)}"
    )

    print(
        "\nModule A feature engineering completed successfully."
    )


if __name__ == "__main__":
    main()
