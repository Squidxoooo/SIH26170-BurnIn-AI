from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# SIH26170 — Module B Feature Engineering
# Early measurements -> 168h prediction
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "components_raw.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "module_b_prediction_features.csv"
)


# ------------------------------------------------------------
# Required columns
# ------------------------------------------------------------

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
    "leakage_168h_uA",

    "propagation_delay_0h_ns",
    "propagation_delay_24h_ns",
    "propagation_delay_168h_ns",

    "leakage_static_limit_uA",
    "delay_static_limit_ns",
]


# ------------------------------------------------------------
# Helper: robust peer Z-score
# ------------------------------------------------------------

def peer_zscore(
    df: pd.DataFrame,
    column: str,
    group_columns: list[str],
) -> pd.Series:

    grouped = df.groupby(
        group_columns,
        dropna=False,
    )[column]

    median = grouped.transform(
        "median"
    )

    mad = grouped.transform(
        lambda x: np.median(
            np.abs(
                x - np.nanmedian(x)
            )
        )
    )

    mad = mad.replace(
        0,
        np.nan,
    )

    z = (
        0.6745
        * (df[column] - median)
        / mad
    )

    return z.fillna(0.0)


# ------------------------------------------------------------
# Load
# ------------------------------------------------------------

def load_data():

    if not RAW_FILE.exists():
        raise FileNotFoundError(
            f"Raw dataset not found:\n{RAW_FILE}"
        )

    df = pd.read_csv(
        RAW_FILE
    )

    missing = sorted(
        set(REQUIRED_COLUMNS)
        - set(df.columns)
    )

    if missing:
        raise ValueError(
            "Missing required columns:\n"
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
# Build prediction features
# ------------------------------------------------------------

def build_features(df):

    result = df.copy()

    # ========================================================
    # EARLY TEMPORAL FEATURES
    # ========================================================

    result["leakage_delta_0_24"] = (
        result["leakage_24h_uA"]
        - result["leakage_0h_uA"]
    )

    result["delay_delta_0_24"] = (
        result["propagation_delay_24h_ns"]
        - result["propagation_delay_0h_ns"]
    )

    result["leakage_relative_change_0_24"] = (
        result["leakage_delta_0_24"]
        / result["leakage_0h_uA"]
        .abs()
        .clip(lower=1e-9)
    )

    result["delay_relative_change_0_24"] = (
        result["delay_delta_0_24"]
        / result["propagation_delay_0h_ns"]
        .abs()
        .clip(lower=1e-9)
    )

    result["leakage_early_slope_uA_per_hour"] = (
        result["leakage_delta_0_24"]
        / 24.0
    )

    result["delay_early_slope_ns_per_hour"] = (
        result["delay_delta_0_24"]
        / 24.0
    )


    # ========================================================
    # EARLY PEER FEATURES
    # ========================================================

    peer_group = [
        "batch_id",
        "device_family",
    ]

    result["leakage_peer_z_0h"] = peer_zscore(
        result,
        "leakage_0h_uA",
        peer_group,
    )

    result["leakage_peer_z_24h"] = peer_zscore(
        result,
        "leakage_24h_uA",
        peer_group,
    )

    result["delay_peer_z_0h"] = peer_zscore(
        result,
        "propagation_delay_0h_ns",
        peer_group,
    )

    result["delay_peer_z_24h"] = peer_zscore(
        result,
        "propagation_delay_24h_ns",
        peer_group,
    )

    result["leakage_peer_z_change"] = peer_zscore(
        result,
        "leakage_delta_0_24",
        peer_group,
    )

    result["delay_peer_z_change"] = peer_zscore(
        result,
        "delay_delta_0_24",
        peer_group,
    )


    # ========================================================
    # EARLY DISTANCE FROM STATIC LIMIT
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
    # BEHAVIOUR / DRIFT FEATURES
    # ========================================================

    result["leakage_change_to_baseline_ratio"] = (
        result["leakage_delta_0_24"].abs()
        / result["leakage_0h_uA"]
        .abs()
        .clip(lower=1e-9)
    )

    result["delay_change_to_baseline_ratio"] = (
        result["delay_delta_0_24"].abs()
        / result["propagation_delay_0h_ns"]
        .abs()
        .clip(lower=1e-9)
    )


    # ========================================================
    # COMBINED EARLY RISK FEATURES
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

    result["max_abs_change_z"] = result[
        [
            "leakage_peer_z_change",
            "delay_peer_z_change",
        ]
    ].abs().max(axis=1)


    # ========================================================
    # FINAL FEATURE TABLE
    # ========================================================

    feature_columns = [
        # Identity/context
        "component_id",
        "batch_id",
        "device_family",
        "chamber_id",

        # Environment
        "ambient_temp_C",
        "burn_in_temp_C",
        "humidity_pct",

        # Early raw observations
        "leakage_0h_uA",
        "leakage_24h_uA",
        "propagation_delay_0h_ns",
        "propagation_delay_24h_ns",

        # Early temporal behaviour
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

        # Limit proximity
        "leakage_limit_margin_24h_uA",
        "delay_limit_margin_24h_ns",
        "leakage_limit_utilization_24h",
        "delay_limit_utilization_24h",

        # Behaviour strength
        "leakage_change_to_baseline_ratio",
        "delay_change_to_baseline_ratio",
        "max_abs_peer_z",
        "max_abs_change_z",

        # Targets — ONLY for training/evaluation.
        # Never feed these into X during prediction.
        "leakage_168h_uA",
        "propagation_delay_168h_ns",
    ]

    return result[
        feature_columns
    ].copy()


# ------------------------------------------------------------
# Leakage validation
# ------------------------------------------------------------

def validate(df):

    feature_columns = [
        column
        for column in df.columns
        if column not in {
            "component_id",
            "batch_id",
            "device_family",
            "chamber_id",
            "leakage_168h_uA",
            "propagation_delay_168h_ns",
        }
    ]

    forbidden = [
        "96h",
        "168h",
        "ground_truth",
        "behavior_type",
        "static_screen_fail",
    ]

    violations = []

    for column in feature_columns:

        lower = column.lower()

        if any(
            item in lower
            for item in forbidden
        ):
            violations.append(
                column
            )

    if violations:

        raise AssertionError(
            "Future/evaluation information "
            "found in prediction inputs:\n"
            + "\n".join(
                f"  - {column}"
                for column in violations
            )
        )

    print(
        "✓ Prediction inputs use only information available by 24h"
    )

    print(
        "✓ 168h measurements are targets only"
    )

    print(
        "✓ Ground-truth labels are excluded"
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

    features = build_features(
        df
    )

    validate(
        features
    )

    features.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print("\n" + "=" * 60)
    print("MODULE B FEATURE REPORT")
    print("=" * 60)

    print(
        f"Components : {len(features):,}"
    )

    print(
        f"Columns    : {len(features.columns)}"
    )

    print(
        f"Missing cells : "
        f"{features.isna().sum().sum():,}"
    )

    print(
        "\nGenerated:"
    )

    print(
        f"  {OUTPUT_FILE.relative_to(PROJECT_ROOT)}"
    )

    print(
        "\nModule B feature engineering completed."
    )


if __name__ == "__main__":
    main()
