from pathlib import Path
import json

import numpy as np
import pandas as pd


# ============================================================
# SIH26170 — Burn-In Data Preprocessing Pipeline
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
CONFIG_DIR = PROJECT_ROOT / "config"


# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

EARLY_HOURS = [0, 24]
PREDICTION_HORIZON = 168

REQUIRED_RAW_COLUMNS = [
    "component_id",
    "batch_id",
    "device_family",
    "chamber_id",
    "ambient_temp_C",
    "burn_in_temp_C",
    "humidity_pct",
    "leakage_0h_uA",
    "leakage_24h_uA",
    "leakage_96h_uA",
    "leakage_168h_uA",
    "leakage_static_limit_uA",
    "propagation_delay_0h_ns",
    "propagation_delay_24h_ns",
    "propagation_delay_96h_ns",
    "propagation_delay_168h_ns",
    "delay_static_limit_ns",
    "behavior_type",
    "ground_truth_status",
    "static_screen_fail",
]


EVALUATION_ONLY_COLUMNS = {
    "behavior_type",
    "ground_truth_status",
    "static_screen_fail",
}


FUTURE_COLUMNS = {
    "leakage_96h_uA",
    "leakage_168h_uA",
    "propagation_delay_96h_ns",
    "propagation_delay_168h_ns",
}


# ------------------------------------------------------------
# Utility functions
# ------------------------------------------------------------

def require_columns(df: pd.DataFrame, columns: list[str], name: str):
    missing = sorted(set(columns) - set(df.columns))

    if missing:
        raise ValueError(
            f"{name} is missing required columns:\n"
            + "\n".join(f"  - {column}" for column in missing)
        )


def robust_z_score(series: pd.Series) -> pd.Series:
    """
    Robust Z-score using median and MAD.

    z = 0.6745 * (x - median) / MAD

    If MAD is zero, fall back to a small epsilon.
    """

    median = series.median()
    mad = np.median(np.abs(series - median))

    if pd.isna(mad) or mad == 0:
        mad = 1e-9

    return 0.6745 * (series - median) / mad


def add_batch_anomaly_features(
    df: pd.DataFrame,
    measurement_columns: list[str],
) -> pd.DataFrame:

    result = df.copy()

    for column in measurement_columns:

        median_col = f"batch_median_{column}"
        mad_col = f"batch_MAD_{column}"
        z_col = f"robust_z_{column}"

        grouped = result.groupby(
            ["batch_id", "device_family"],
            dropna=False
        )[column]

        result[median_col] = grouped.transform("median")

        result[mad_col] = grouped.transform(
            lambda x: np.median(np.abs(x - np.nanmedian(x)))
        )

        safe_mad = result[mad_col].replace(0, np.nan)

        result[z_col] = (
            0.6745
            * (result[column] - result[median_col])
            / safe_mad
        )

        result[z_col] = result[z_col].fillna(0.0)

    return result


# ------------------------------------------------------------
# Load raw data
# ------------------------------------------------------------

def load_raw_data() -> pd.DataFrame:

    path = RAW_DIR / "components_raw.csv"

    if not path.exists():
        raise FileNotFoundError(
            f"Raw dataset not found:\n{path}"
        )

    df = pd.read_csv(path)

    print(f"Loaded raw dataset: {df.shape[0]:,} rows × {df.shape[1]} columns")

    require_columns(
        df,
        REQUIRED_RAW_COLUMNS,
        "components_raw.csv"
    )

    return df


# ------------------------------------------------------------
# Basic cleaning
# ------------------------------------------------------------

def clean_raw_data(df: pd.DataFrame) -> pd.DataFrame:

    df = df.copy()

    # Normalize boolean field.
    if df["static_screen_fail"].dtype == object:
        df["static_screen_fail"] = (
            df["static_screen_fail"]
            .astype(str)
            .str.strip()
            .str.lower()
            .map({
                "true": True,
                "false": False,
                "1": True,
                "0": False,
            })
        )

    # Numeric columns.
    numeric_columns = [
        column
        for column in df.columns
        if column.endswith("_uA")
        or column.endswith("_ns")
        or column.endswith("_C")
        or column.endswith("_pct")
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    # Remove duplicate component records.
    duplicate_count = df["component_id"].duplicated().sum()

    if duplicate_count:
        print(
            f"WARNING: removing {duplicate_count} duplicate component records"
        )

        df = df.drop_duplicates(
            subset="component_id",
            keep="first"
        )

    # Sort deterministically.
    df = df.sort_values(
        ["batch_id", "component_id"]
    ).reset_index(drop=True)

    return df


# ------------------------------------------------------------
# Module A
# Early peer-based anomaly detection
# ------------------------------------------------------------

def build_module_a(df: pd.DataFrame) -> pd.DataFrame:

    columns = [
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
        "leakage_static_limit_uA",
        "delay_static_limit_ns",
    ]

    result = df[columns].copy()

    measurement_columns = [
        "leakage_0h_uA",
        "leakage_24h_uA",
        "propagation_delay_0h_ns",
        "propagation_delay_24h_ns",
    ]

    result = add_batch_anomaly_features(
        result,
        measurement_columns
    )

    # Combine the strongest observed early anomaly.
    z_columns = [
        f"robust_z_{column}"
        for column in measurement_columns
    ]

    result["max_early_abs_robust_z"] = (
        result[z_columns]
        .abs()
        .max(axis=1)
    )

    # Do NOT classify as defective here.
    # Module A produces an anomaly score;
    # the risk engine will decide the operational state.
    result["anomaly_score"] = np.clip(
        result["max_early_abs_robust_z"] / 8.0,
        0.0,
        1.0,
    )

    return result


# ------------------------------------------------------------
# Module B
# Early measurements → 168h prediction
# ------------------------------------------------------------

def build_module_b(df: pd.DataFrame) -> pd.DataFrame:

    columns = [
        "component_id",
        "batch_id",
        "device_family",
        "chamber_id",
        "ambient_temp_C",
        "burn_in_temp_C",
        "humidity_pct",

        # EARLY INPUTS
        "leakage_0h_uA",
        "leakage_24h_uA",
        "propagation_delay_0h_ns",
        "propagation_delay_24h_ns",

        # TARGETS — never use these as input features
        "leakage_168h_uA",
        "propagation_delay_168h_ns",
    ]

    result = df[columns].copy()

    # Only rows with future targets can be used for supervised regression.
    result = result.dropna(
        subset=[
            "leakage_168h_uA",
            "propagation_delay_168h_ns",
        ]
    )

    # Grouped split.
    #
    # IMPORTANT:
    # Never randomly split individual components from the same batch.
    # That would let the model see almost identical lot distributions
    # during training and testing.
    test_batches = [
        "B09",
        "B10",
        "B11",
        "B20",
    ]

    result["split"] = np.where(
        result["batch_id"].isin(test_batches),
        "test",
        "train",
    )

    return result.reset_index(drop=True)


# ------------------------------------------------------------
# Evaluation labels
# ------------------------------------------------------------

def build_evaluation_labels(df: pd.DataFrame) -> pd.DataFrame:

    columns = [
        "component_id",
        "batch_id",
        "behavior_type",
        "ground_truth_status",
        "static_screen_fail",
    ]

    return df[columns].copy()


# ------------------------------------------------------------
# Validation
# ------------------------------------------------------------

def validate_no_leakage(
    module_a: pd.DataFrame,
    module_b: pd.DataFrame,
):

    print("\nRunning leakage checks...")

    # Module A must not contain future measurements.
    module_a_future = (
        set(module_a.columns)
        & FUTURE_COLUMNS
    )

    if module_a_future:
        raise AssertionError(
            "MODULE A LEAKAGE: "
            f"{sorted(module_a_future)}"
        )

    # Module B inputs.
    forbidden_module_b_inputs = (
        FUTURE_COLUMNS
        | EVALUATION_ONLY_COLUMNS
    )

    # These are targets, so they are allowed in the dataset
    # but must never be passed to model.predict().
    module_b_targets = {
        "leakage_168h_uA",
        "propagation_delay_168h_ns",
    }

    actual_forbidden = (
        set(module_b.columns)
        & forbidden_module_b_inputs
    ) - module_b_targets

    if actual_forbidden:
        raise AssertionError(
            "MODULE B LEAKAGE: "
            f"{sorted(actual_forbidden)}"
        )

    print("✓ No future measurements used by Module A")
    print("✓ Evaluation labels excluded from ML datasets")
    print("✓ Module B keeps 168h values only as targets")


# ------------------------------------------------------------
# Dataset report
# ------------------------------------------------------------

def print_report(
    raw: pd.DataFrame,
    module_a: pd.DataFrame,
    module_b: pd.DataFrame,
    labels: pd.DataFrame,
):

    print("\n" + "=" * 60)
    print("SIH26170 DATASET REPORT")
    print("=" * 60)

    print(f"Raw components       : {len(raw):,}")
    print(f"Module A rows        : {len(module_a):,}")
    print(f"Module B rows        : {len(module_b):,}")

    print(
        f"Training rows        : "
        f"{(module_b['split'] == 'train').sum():,}"
    )

    print(
        f"Testing rows         : "
        f"{(module_b['split'] == 'test').sum():,}"
    )

    print(
        f"Missing raw values   : "
        f"{raw.isna().sum().sum():,}"
    )

    print(
        f"Duplicate components : "
        f"{raw['component_id'].duplicated().sum():,}"
    )

    print("\nDevice families:")

    print(
        raw["device_family"]
        .value_counts()
        .to_string()
    )

    print("\nGround truth:")

    print(
        labels["ground_truth_status"]
        .value_counts()
        .to_string()
    )

    print("\nBehavior types:")

    print(
        labels["behavior_type"]
        .value_counts()
        .to_string()
    )

    print("\n" + "=" * 60)


# ------------------------------------------------------------
# Main pipeline
# ------------------------------------------------------------

def main():

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    raw = load_raw_data()

    raw = clean_raw_data(raw)

    module_a = build_module_a(raw)

    module_b = build_module_b(raw)

    labels = build_evaluation_labels(raw)

    validate_no_leakage(
        module_a,
        module_b
    )

    # Save outputs.
    module_a.to_csv(
        PROCESSED_DIR / "module_a_features.csv",
        index=False
    )

    module_b.to_csv(
        PROCESSED_DIR / "module_b_regression.csv",
        index=False
    )

    labels.to_csv(
        PROCESSED_DIR / "evaluation_labels.csv",
        index=False
    )

    print_report(
        raw,
        module_a,
        module_b,
        labels,
    )

    print("\nGenerated:")
    print("  data/processed/module_a_features.csv")
    print("  data/processed/module_b_regression.csv")
    print("  data/processed/evaluation_labels.csv")
    print("\nPipeline completed successfully.")


if __name__ == "__main__":
    main()
