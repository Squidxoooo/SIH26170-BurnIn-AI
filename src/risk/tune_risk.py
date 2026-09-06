from pathlib import Path
import json
import itertools

import numpy as np
import pandas as pd


# ============================================================
# SIH26170 — Risk Policy Tuning
#
# IMPORTANT:
# Risk thresholds are tuned ONLY on validation batches.
#
# Validation:
#   B06, B13, B17
#
# Final test:
#   B09, B10, B11, B20
#
# Final test data is never used here.
# ============================================================


PROJECT_ROOT = Path(__file__).resolve().parents[2]

VALIDATION_FILE = (
    PROJECT_ROOT
    / "reports"
    / "risk"
    / "validation_predictions.csv"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "reports"
    / "risk"
)

CONFIG_DIR = (
    PROJECT_ROOT
    / "config"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

CONFIG_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# Evaluation groups
# ============================================================

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


# ============================================================
# Threshold search space
# ============================================================

ANOMALY_WATCH_VALUES = [
    0.20,
    0.30,
    0.40,
    0.50,
]

ANOMALY_HIGH_VALUES = [
    0.50,
    0.60,
    0.70,
    0.80,
]

LEAKAGE_UTIL_WATCH_VALUES = [
    0.75,
    0.80,
    0.85,
    0.90,
    0.95,
]

LEAKAGE_UTIL_HIGH_VALUES = [
    0.90,
    0.95,
    1.00,
    1.05,
]

LEAKAGE_SLOPE_WATCH_VALUES = [
    0.010,
    0.015,
    0.020,
    0.025,
]

LEAKAGE_SLOPE_HIGH_VALUES = [
    0.025,
    0.030,
    0.040,
    0.050,
]


# ============================================================
# Safety / practicality constraints
# ============================================================

# Maximum fraction of healthy components allowed to be RED.
MAX_HEALTHY_RED_RATE = 0.05

# Maximum fraction of all validation components that may be
# WATCH or RED.
MAX_TOTAL_ALERT_RATE = 0.60


# ============================================================
# Load validation predictions
# ============================================================

def load_validation_data():

    if not VALIDATION_FILE.exists():
        raise FileNotFoundError(
            f"Validation predictions not found:\n"
            f"{VALIDATION_FILE}"
        )

    df = pd.read_csv(
        VALIDATION_FILE
    )

    required = [
        "component_id",
        "batch_id",
        "device_family",

        "anomaly_score",

        "predicted_leakage_168h_uA",
        "predicted_delay_168h_ns",

        "predicted_leakage_slope_uA_per_hour",
        "predicted_delay_slope_ns_per_hour",

        "leakage_static_limit_uA",
        "delay_static_limit_ns",

        "ground_truth_status",
        "static_screen_fail",
    ]

    missing = sorted(
        set(required) - set(df.columns)
    )

    if missing:
        raise ValueError(
            "Validation file is missing columns:\n"
            + "\n".join(
                f"  - {column}"
                for column in missing
            )
        )

    # Safety check:
    # this script must only contain validation batches.
    found_batches = set(
        df["batch_id"].dropna().unique()
    )

    unexpected = (
        found_batches
        & FINAL_TEST_BATCHES
    )

    if unexpected:
        raise AssertionError(
            "FINAL TEST BATCHES FOUND IN VALIDATION DATA:\n"
            + ", ".join(sorted(unexpected))
        )

    return df


# ============================================================
# Prepare engineering signals
# ============================================================

def prepare_signals(df):

    result = df.copy()

    result[
        "predicted_leakage_utilization"
    ] = (
        result[
            "predicted_leakage_168h_uA"
        ]
        / result[
            "leakage_static_limit_uA"
        ]
    )

    result[
        "predicted_delay_utilization"
    ] = (
        result[
            "predicted_delay_168h_ns"
        ]
        / result[
            "delay_static_limit_ns"
        ]
    )

    # A latent defect is a defective component that passed
    # the conventional static screen.
    result["is_latent_defect"] = (
        (result["ground_truth_status"] == "Defective")
        &
        (~result["static_screen_fail"].fillna(False))
    )

    result["is_healthy"] = (
        result["ground_truth_status"] == "Healthy"
    )

    return result


# ============================================================
# Apply one candidate policy
# ============================================================

def apply_policy(
    df,
    anomaly_watch,
    anomaly_high,
    leakage_util_watch,
    leakage_util_high,
    leakage_slope_watch,
    leakage_slope_high,
):

    result = df.copy()

    # --------------------------------------------------------
    # HIGH conditions
    # --------------------------------------------------------

    high = (
        (result["anomaly_score"] >= anomaly_high)
        |
        (
            result["predicted_leakage_utilization"]
            >= leakage_util_high
        )
        |
        (
            result[
                "predicted_leakage_slope_uA_per_hour"
            ]
            >= leakage_slope_high
        )
    )

    # --------------------------------------------------------
    # WATCH conditions
    # --------------------------------------------------------

    watch = (
        (result["anomaly_score"] >= anomaly_watch)
        |
        (
            result["predicted_leakage_utilization"]
            >= leakage_util_watch
        )
        |
        (
            result[
                "predicted_leakage_slope_uA_per_hour"
            ]
            >= leakage_slope_watch
        )
    )

    # HIGH always wins over WATCH.
    result["risk_level"] = np.where(
        high,
        "HIGH",
        np.where(
            watch,
            "WATCH",
            "NORMAL",
        ),
    )

    return result


# ============================================================
# Evaluate a candidate policy
# ============================================================

def evaluate_policy(
    df,
    anomaly_watch,
    anomaly_high,
    leakage_util_watch,
    leakage_util_high,
    leakage_slope_watch,
    leakage_slope_high,
):

    scored = apply_policy(
        df,
        anomaly_watch,
        anomaly_high,
        leakage_util_watch,
        leakage_util_high,
        leakage_slope_watch,
        leakage_slope_high,
    )

    latent = scored[
        "is_latent_defect"
    ]

    healthy = scored[
        "is_healthy"
    ]

    normal = (
        scored["risk_level"] == "NORMAL"
    )

    watch = (
        scored["risk_level"] == "WATCH"
    )

    high = (
        scored["risk_level"] == "HIGH"
    )

    total_defects = int(
        latent.sum()
    )

    total_healthy = int(
        healthy.sum()
    )

    defective_green = int(
        (latent & normal).sum()
    )

    defective_watch = int(
        (latent & watch).sum()
    )

    defective_red = int(
        (latent & high).sum()
    )

    healthy_green = int(
        (healthy & normal).sum()
    )

    healthy_watch = int(
        (healthy & watch).sum()
    )

    healthy_red = int(
        (healthy & high).sum()
    )

    defective_green_rate = (
        defective_green / total_defects
        if total_defects
        else 1.0
    )

    defective_capture_rate = (
        1.0 - defective_green_rate
    )

    healthy_red_rate = (
        healthy_red / total_healthy
        if total_healthy
        else 1.0
    )

    total_alert_rate = float(
        (watch | high).mean()
    )

    red_precision = (
        defective_red
        / (defective_red + healthy_red)
        if (defective_red + healthy_red)
        else 0.0
    )

    watch_or_high_capture = (
        (defective_watch + defective_red)
        / total_defects
        if total_defects
        else 0.0
    )

    high_capture = (
        defective_red / total_defects
        if total_defects
        else 0.0
    )

    return {
        "anomaly_watch": anomaly_watch,
        "anomaly_high": anomaly_high,

        "leakage_util_watch":
            leakage_util_watch,

        "leakage_util_high":
            leakage_util_high,

        "leakage_slope_watch":
            leakage_slope_watch,

        "leakage_slope_high":
            leakage_slope_high,

        "defective_green":
            defective_green,

        "defective_watch":
            defective_watch,

        "defective_red":
            defective_red,

        "defective_green_rate":
            defective_green_rate,

        "defective_capture_rate":
            defective_capture_rate,

        "watch_or_high_capture":
            watch_or_high_capture,

        "high_capture":
            high_capture,

        "healthy_green":
            healthy_green,

        "healthy_watch":
            healthy_watch,

        "healthy_red":
            healthy_red,

        "healthy_red_rate":
            healthy_red_rate,

        "total_alert_rate":
            total_alert_rate,

        "red_precision":
            red_precision,
    }


# ============================================================
# Search all valid policies
# ============================================================

def search_policies(df):

    candidates = []

    total_combinations = (
        len(ANOMALY_WATCH_VALUES)
        * len(ANOMALY_HIGH_VALUES)
        * len(LEAKAGE_UTIL_WATCH_VALUES)
        * len(LEAKAGE_UTIL_HIGH_VALUES)
        * len(LEAKAGE_SLOPE_WATCH_VALUES)
        * len(LEAKAGE_SLOPE_HIGH_VALUES)
    )

    print(
        f"Searching {total_combinations:,} "
        "candidate policies..."
    )

    for (
        anomaly_watch,
        anomaly_high,
        leakage_util_watch,
        leakage_util_high,
        leakage_slope_watch,
        leakage_slope_high,
    ) in itertools.product(
        ANOMALY_WATCH_VALUES,
        ANOMALY_HIGH_VALUES,
        LEAKAGE_UTIL_WATCH_VALUES,
        LEAKAGE_UTIL_HIGH_VALUES,
        LEAKAGE_SLOPE_WATCH_VALUES,
        LEAKAGE_SLOPE_HIGH_VALUES,
    ):

        # High threshold must be stricter than Watch.
        if anomaly_high <= anomaly_watch:
            continue

        if leakage_util_high <= leakage_util_watch:
            continue

        if leakage_slope_high <= leakage_slope_watch:
            continue

        metrics = evaluate_policy(
            df,
            anomaly_watch,
            anomaly_high,
            leakage_util_watch,
            leakage_util_high,
            leakage_slope_watch,
            leakage_slope_high,
        )

        # ----------------------------------------------------
        # Constraint 1:
        # don't flood healthy components with RED.
        # ----------------------------------------------------

        if (
            metrics["healthy_red_rate"]
            > MAX_HEALTHY_RED_RATE
        ):
            continue

        # ----------------------------------------------------
        # Constraint 2:
        # don't turn most of the batch into alerts.
        # ----------------------------------------------------

        if (
            metrics["total_alert_rate"]
            > MAX_TOTAL_ALERT_RATE
        ):
            continue

        candidates.append(
            metrics
        )

    return pd.DataFrame(
        candidates
    )


# ============================================================
# Select best policy
# ============================================================

def select_best(
    candidates,
):

    if candidates.empty:
        raise RuntimeError(
            "No policy satisfied the configured "
            "safety constraints."
        )

    # Priority:
    #
    # 1. Minimize defective -> NORMAL.
    # 2. Maximize defective capture.
    # 3. Prefer higher RED precision.
    # 4. Prefer fewer overall alerts.
    #
    # This means missing a defective component is treated
    # as more serious than creating an extra WATCH alert.

    ordered = candidates.sort_values(
        [
            "defective_green_rate",
            "defective_capture_rate",
            "red_precision",
            "total_alert_rate",
        ],
        ascending=[
            True,
            False,
            False,
            True,
        ],
    )

    return ordered.iloc[0]


# ============================================================
# Build explainable validation assessment
# ============================================================

def build_assessment(
    df,
    best,
):

    result = apply_policy(
        df,
        best["anomaly_watch"],
        best["anomaly_high"],
        best["leakage_util_watch"],
        best["leakage_util_high"],
        best["leakage_slope_watch"],
        best["leakage_slope_high"],
    )

    reasons = []

    for _, row in result.iterrows():

        high_reasons = []
        watch_reasons = []

        # ----------------------------------------------
        # Early anomaly
        # ----------------------------------------------

        if (
            row["anomaly_score"]
            >= best["anomaly_high"]
        ):
            high_reasons.append(
                "High early anomaly"
            )

        elif (
            row["anomaly_score"]
            >= best["anomaly_watch"]
        ):
            watch_reasons.append(
                "Elevated early anomaly"
            )

        # ----------------------------------------------
        # Predicted leakage
        # ----------------------------------------------

        if (
            row[
                "predicted_leakage_utilization"
            ]
            >= best["leakage_util_high"]
        ):
            high_reasons.append(
                "Predicted leakage reaches/exceeds "
                "configured high threshold"
            )

        elif (
            row[
                "predicted_leakage_utilization"
            ]
            >= best["leakage_util_watch"]
        ):
            watch_reasons.append(
                "Predicted leakage approaches limit"
            )

        # ----------------------------------------------
        # Predicted leakage slope
        # ----------------------------------------------

        if (
            row[
                "predicted_leakage_slope_uA_per_hour"
            ]
            >= best["leakage_slope_high"]
        ):
            high_reasons.append(
                "Projected leakage drift exceeds "
                "configured high threshold"
            )

        elif (
            row[
                "predicted_leakage_slope_uA_per_hour"
            ]
            >= best["leakage_slope_watch"]
        ):
            watch_reasons.append(
                "Elevated projected leakage drift"
            )

        if high_reasons:
            reason = " | ".join(
                high_reasons
            )

        elif watch_reasons:
            reason = " | ".join(
                watch_reasons
            )

        else:
            reason = (
                "Early behaviour and predicted "
                "trajectory remain within "
                "configured thresholds"
            )

        reasons.append(
            reason
        )

    result["risk_reason"] = reasons

    result["risk_status"] = (
        result["risk_level"].map(
            {
                "NORMAL": "GREEN",
                "WATCH": "YELLOW",
                "HIGH": "RED",
            }
        )
    )

    return result


# ============================================================
# Main
# ============================================================

def main():

    print("=" * 60)
    print("SIH26170 — RISK POLICY TUNING")
    print("=" * 60)

    df = load_validation_data()

    df = prepare_signals(
        df
    )

    print(
        f"\nValidation components : "
        f"{len(df):,}"
    )

    print(
        f"Validation batches    : "
        f"{sorted(df['batch_id'].unique())}"
    )

    print(
        f"Latent defects        : "
        f"{df['is_latent_defect'].sum():,}"
    )

    print(
        f"Healthy components    : "
        f"{df['is_healthy'].sum():,}"
    )

    print(
        "\nFinal test batches are protected:"
    )

    print(
        f"  {sorted(FINAL_TEST_BATCHES)}"
    )

    # --------------------------------------------------------
    # Search
    # --------------------------------------------------------

    candidates = search_policies(
        df
    )

    print(
        f"\nValid policies: "
        f"{len(candidates):,}"
    )

    if candidates.empty:
        raise RuntimeError(
            "No valid risk policy found."
        )

    # --------------------------------------------------------
    # Pick best
    # --------------------------------------------------------

    best = select_best(
        candidates
    )

    print("\n" + "=" * 60)
    print("BEST VALIDATION RISK POLICY")
    print("=" * 60)

    print(
        f"Anomaly WATCH        : "
        f"{best['anomaly_watch']:.3f}"
    )

    print(
        f"Anomaly HIGH         : "
        f"{best['anomaly_high']:.3f}"
    )

    print(
        f"Leakage WATCH        : "
        f"{best['leakage_util_watch']:.3f}"
    )

    print(
        f"Leakage HIGH         : "
        f"{best['leakage_util_high']:.3f}"
    )

    print(
        f"Leakage slope WATCH  : "
        f"{best['leakage_slope_watch']:.4f}"
    )

    print(
        f"Leakage slope HIGH   : "
        f"{best['leakage_slope_high']:.4f}"
    )

    print("\nValidation performance:")

    print(
        f"Defective -> GREEN : "
        f"{int(best['defective_green'])}"
    )

    print(
        f"Defective -> WATCH : "
        f"{int(best['defective_watch'])}"
    )

    print(
        f"Defective -> RED   : "
        f"{int(best['defective_red'])}"
    )

    print(
        f"\nDefective GREEN rate : "
        f"{best['defective_green_rate']:.3f}"
    )

    print(
        f"Defective captured "
        f"(WATCH + RED)      : "
        f"{best['watch_or_high_capture']:.3f}"
    )

    print(
        f"RED precision        : "
        f"{best['red_precision']:.3f}"
    )

    print(
        f"Healthy RED rate     : "
        f"{best['healthy_red_rate']:.3f}"
    )

    print(
        f"Total alert rate     : "
        f"{best['total_alert_rate']:.3f}"
    )

    # --------------------------------------------------------
    # Save all candidate policies
    # --------------------------------------------------------

    benchmark_file = (
        OUTPUT_DIR
        / "risk_policy_candidates.csv"
    )

    candidates.to_csv(
        benchmark_file,
        index=False,
    )

    # --------------------------------------------------------
    # Save frozen policy
    # --------------------------------------------------------

    policy = {
        "version": "validation-tuned-v1",

        "anomaly_watch":
            float(best["anomaly_watch"]),

        "anomaly_high":
            float(best["anomaly_high"]),

        "leakage_utilization_watch":
            float(best["leakage_util_watch"]),

        "leakage_utilization_high":
            float(best["leakage_util_high"]),

        "leakage_slope_watch_uA_per_hour":
            float(best["leakage_slope_watch"]),

        "leakage_slope_high_uA_per_hour":
            float(best["leakage_slope_high"]),

        "max_healthy_red_rate":
            MAX_HEALTHY_RED_RATE,

        "max_total_alert_rate":
            MAX_TOTAL_ALERT_RATE,

        "validation_batches": sorted(
            VALIDATION_BATCHES
        ),

        "final_test_batches": sorted(
            FINAL_TEST_BATCHES
        ),

        "note": (
            "Thresholds tuned on validation batches only. "
            "Slope thresholds are prototype engineering "
            "thresholds and are not official ISRO specifications."
        ),
    }

    policy_file = (
        CONFIG_DIR
        / "model_rules.json"
    )

    policy_file.write_text(
        json.dumps(
            policy,
            indent=2,
        )
    )

    # --------------------------------------------------------
    # Save validation assessment
    # --------------------------------------------------------

    assessment = build_assessment(
        df,
        best,
    )

    assessment_file = (
        OUTPUT_DIR
        / "validation_risk_assessment.csv"
    )

    assessment.to_csv(
        assessment_file,
        index=False,
    )

    # --------------------------------------------------------
    # Final validation distribution
    # --------------------------------------------------------

    distribution = (
        assessment["risk_level"]
        .value_counts()
        .reindex(
            [
                "NORMAL",
                "WATCH",
                "HIGH",
            ],
            fill_value=0,
        )
    )

    print(
        "\nValidation risk distribution:"
    )

    print(
        distribution.to_string()
    )

    print("\nSaved:")

    print(
        f"  {benchmark_file.relative_to(PROJECT_ROOT)}"
    )

    print(
        f"  {policy_file.relative_to(PROJECT_ROOT)}"
    )

    print(
        f"  {assessment_file.relative_to(PROJECT_ROOT)}"
    )

    print(
        "\nRisk policy tuning completed successfully."
    )


if __name__ == "__main__":
    main()
