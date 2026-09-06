from pathlib import Path
import json

import numpy as np
import pandas as pd


# ============================================================
# SIH26170 — Risk Engine
#
# Module A + Module B + frozen risk policy
#                         ↓
#             NORMAL / WATCH / HIGH RISK
#
# Risk policy is loaded from:
#     config/model_rules.json
#
# The policy was tuned ONLY on validation batches.
# ============================================================


PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "components_raw.csv"
)

MODULE_A_FILE = (
    PROJECT_ROOT
    / "reports"
    / "eda"
    / "module_a_test_predictions.csv"
)

MODULE_B_FILE = (
    PROJECT_ROOT
    / "reports"
    / "prediction"
    / "module_b_v2_predictions.csv"
)

CONFIG_FILE = (
    PROJECT_ROOT
    / "config"
    / "model_rules.json"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "reports"
    / "risk"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "risk_assessment.csv"
)

SUMMARY_FILE = (
    OUTPUT_DIR
    / "risk_summary.csv"
)


OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# Load frozen policy
# ============================================================

def load_policy():

    if not CONFIG_FILE.exists():
        raise FileNotFoundError(
            f"Risk policy not found:\n{CONFIG_FILE}"
        )

    with CONFIG_FILE.open("r") as f:
        policy = json.load(f)

    required = [
        "anomaly_watch",
        "anomaly_high",
        "leakage_utilization_watch",
        "leakage_utilization_high",
        "leakage_slope_watch_uA_per_hour",
        "leakage_slope_high_uA_per_hour",
    ]

    missing = [
        key
        for key in required
        if key not in policy
    ]

    if missing:
        raise ValueError(
            "Risk policy is missing keys:\n"
            + "\n".join(
                f"  - {key}"
                for key in missing
            )
        )

    return policy


# ============================================================
# Load datasets
# ============================================================

def load_data():

    for path in [
        RAW_FILE,
        MODULE_A_FILE,
        MODULE_B_FILE,
    ]:

        if not path.exists():
            raise FileNotFoundError(
                f"Required file not found:\n{path}"
            )

    raw = pd.read_csv(
        RAW_FILE
    )

    module_a = pd.read_csv(
        MODULE_A_FILE
    )

    module_b = pd.read_csv(
        MODULE_B_FILE
    )

    return (
        raw,
        module_a,
        module_b,
    )


# ============================================================
# Build combined component table
# ============================================================

def build_assessment(
    raw,
    module_a,
    module_b,
):

    # --------------------------------------------------------
    # Static engineering limits
    # --------------------------------------------------------

    limits = raw[
        [
            "component_id",
            "batch_id",
            "device_family",
            "leakage_static_limit_uA",
            "delay_static_limit_ns",
        ]
    ].drop_duplicates(
        subset=[
            "component_id",
            "batch_id",
        ]
    )

    # --------------------------------------------------------
    # Module A output
    # --------------------------------------------------------

    anomaly_columns = [
        "component_id",
        "batch_id",
        "anomaly_score",
    ]

    anomaly = module_a[
        anomaly_columns
    ].copy()

    # --------------------------------------------------------
    # Module B output
    # --------------------------------------------------------

    prediction_columns = [
        "component_id",
        "batch_id",
        "predicted_leakage_168h_uA",
        "predicted_delay_168h_ns",
        "predicted_leakage_slope_uA_per_hour",
        "predicted_delay_slope_ns_per_hour",
    ]

    prediction = module_b[
        prediction_columns
    ].copy()

    # --------------------------------------------------------
    # Merge all signals
    # --------------------------------------------------------

    result = (
        limits
        .merge(
            anomaly,
            on=[
                "component_id",
                "batch_id",
            ],
            how="inner",
        )
        .merge(
            prediction,
            on=[
                "component_id",
                "batch_id",
            ],
            how="inner",
        )
    )

    if result.empty:
        raise ValueError(
            "No components were found in both "
            "Module A and Module B outputs."
        )

    return result


# ============================================================
# Calculate engineering signals
# ============================================================

def calculate_signals(
    df,
    policy,
):

    result = df.copy()

    # --------------------------------------------------------
    # Predicted future utilization
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Threshold signals
    # --------------------------------------------------------

    result["anomaly_watch"] = (
        result["anomaly_score"]
        >= policy["anomaly_watch"]
    )

    result["anomaly_high"] = (
        result["anomaly_score"]
        >= policy["anomaly_high"]
    )

    result["leakage_limit_watch"] = (
        result[
            "predicted_leakage_utilization"
        ]
        >= policy[
            "leakage_utilization_watch"
        ]
    )

    result["leakage_limit_high"] = (
        result[
            "predicted_leakage_utilization"
        ]
        >= policy[
            "leakage_utilization_high"
        ]
    )

    result["leakage_slope_watch"] = (
        result[
            "predicted_leakage_slope_uA_per_hour"
        ]
        >= policy[
            "leakage_slope_watch_uA_per_hour"
        ]
    )

    result["leakage_slope_high"] = (
        result[
            "predicted_leakage_slope_uA_per_hour"
        ]
        >= policy[
            "leakage_slope_high_uA_per_hour"
        ]
    )

    return result


# ============================================================
# Risk classification
# ============================================================

def classify_risk(
    df,
):

    result = df.copy()

    # --------------------------------------------------------
    # HIGH:
    # any high-severity signal.
    # --------------------------------------------------------

    high = (
        result["anomaly_high"]
        |
        result["leakage_limit_high"]
        |
        result["leakage_slope_high"]
    )

    # --------------------------------------------------------
    # WATCH:
    # any elevated signal.
    # --------------------------------------------------------

    watch = (
        result["anomaly_watch"]
        |
        result["leakage_limit_watch"]
        |
        result["leakage_slope_watch"]
    )

    result["risk_level"] = np.where(
        high,
        "HIGH",
        np.where(
            watch,
            "WATCH",
            "NORMAL",
        ),
    )

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
# Composite risk score
# ============================================================

def calculate_risk_score(
    df,
    policy,
):

    result = df.copy()

    # --------------------------------------------------------
    # Anomaly contribution
    # --------------------------------------------------------

    anomaly_component = np.clip(
        result["anomaly_score"],
        0.0,
        1.0,
    )

    # --------------------------------------------------------
    # Predicted leakage contribution
    # --------------------------------------------------------

    leakage_component = np.clip(
        result[
            "predicted_leakage_utilization"
        ],
        0.0,
        1.25,
    ) / 1.25

    # --------------------------------------------------------
    # Predicted drift contribution
    # --------------------------------------------------------

    slope_component = np.clip(
        result[
            "predicted_leakage_slope_uA_per_hour"
        ]
        / policy[
            "leakage_slope_high_uA_per_hour"
        ],
        0.0,
        1.25,
    ) / 1.25

    # --------------------------------------------------------
    # Delay contribution
    #
    # Delay is not used as a classification trigger in the
    # tuned policy, but is retained in the composite score
    # as additional context.
    # --------------------------------------------------------

    delay_component = np.clip(
        result[
            "predicted_delay_utilization"
        ],
        0.0,
        1.25,
    ) / 1.25

    # --------------------------------------------------------
    # Weighted score
    # --------------------------------------------------------

    result["risk_score"] = (
        0.40 * anomaly_component
        + 0.35 * leakage_component
        + 0.20 * slope_component
        + 0.05 * delay_component
    )

    result["risk_score"] = np.clip(
        result["risk_score"],
        0.0,
        1.0,
    )

    return result


# ============================================================
# Explainability
# ============================================================

def build_reasons(
    row,
    policy,
):

    reasons = []

    # --------------------------------------------------------
    # Early anomaly
    # --------------------------------------------------------

    if row["anomaly_high"]:

        reasons.append(
            "High early anomaly"
        )

    elif row["anomaly_watch"]:

        reasons.append(
            "Elevated early anomaly"
        )

    # --------------------------------------------------------
    # Predicted leakage
    # --------------------------------------------------------

    if row["leakage_limit_high"]:

        reasons.append(
            "Predicted 168h leakage approaches/exceeds "
            "configured high threshold"
        )

    elif row["leakage_limit_watch"]:

        reasons.append(
            "Predicted 168h leakage approaches static limit"
        )

    # --------------------------------------------------------
    # Predicted leakage drift
    # --------------------------------------------------------

    if row["leakage_slope_high"]:

        reasons.append(
            "Projected leakage drift exceeds "
            "configured high threshold"
        )

    elif row["leakage_slope_watch"]:

        reasons.append(
            "Elevated projected leakage drift"
        )

    if not reasons:

        reasons.append(
            "Early behaviour and predicted trajectory "
            "remain within configured thresholds"
        )

    return " | ".join(
        reasons
    )


# ============================================================
# Generate summary
# ============================================================

def generate_summary(
    result,
):

    counts = (
        result["risk_level"]
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

    summary = pd.DataFrame(
        {
            "risk_level": counts.index,
            "count": counts.values,
        }
    )

    summary["percentage"] = (
        summary["count"]
        / len(result)
        * 100.0
    )

    return summary


# ============================================================
# Main
# ============================================================

def main():

    print(
        "Loading frozen risk policy..."
    )

    policy = load_policy()

    print(
        f"  Anomaly WATCH       : "
        f"{policy['anomaly_watch']:.3f}"
    )

    print(
        f"  Anomaly HIGH        : "
        f"{policy['anomaly_high']:.3f}"
    )

    print(
        f"  Leakage WATCH       : "
        f"{policy['leakage_utilization_watch']:.3f}"
    )

    print(
        f"  Leakage HIGH        : "
        f"{policy['leakage_utilization_high']:.3f}"
    )

    print(
        f"  Leakage slope WATCH : "
        f"{policy['leakage_slope_watch_uA_per_hour']:.4f}"
    )

    print(
        f"  Leakage slope HIGH  : "
        f"{policy['leakage_slope_high_uA_per_hour']:.4f}"
    )

    print(
        "\nLoading Module A, Module B, and engineering limits..."
    )

    raw, module_a, module_b = load_data()

    print(
        f"  Raw components : {len(raw):,}"
    )

    print(
        f"  Module A rows  : {len(module_a):,}"
    )

    print(
        f"  Module B rows  : {len(module_b):,}"
    )

    print(
        "\nBuilding combined assessment..."
    )

    result = build_assessment(
        raw,
        module_a,
        module_b,
    )

    print(
        f"  Components assessed : "
        f"{len(result):,}"
    )

    print(
        "\nCalculating engineering signals..."
    )

    result = calculate_signals(
        result,
        policy,
    )

    print(
        "Classifying risk..."
    )

    result = classify_risk(
        result,
    )

    print(
        "Calculating composite risk score..."
    )

    result = calculate_risk_score(
        result,
        policy,
    )

    # --------------------------------------------------------
    # Explainability
    # --------------------------------------------------------

    result["risk_reason"] = result.apply(
        lambda row: build_reasons(
            row,
            policy,
        ),
        axis=1,
    )

    # Highest risk first.
    result = result.sort_values(
        [
            "risk_score",
            "anomaly_score",
        ],
        ascending=False,
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    summary = generate_summary(
        result
    )

    print("\n" + "=" * 60)
    print("SIH26170 — RISK ENGINE")
    print("=" * 60)

    print(
        f"Components assessed : "
        f"{len(result):,}"
    )

    print(
        "\nRisk distribution:"
    )

    for _, row in summary.iterrows():

        print(
            f"  {row['risk_level']:7s} : "
            f"{int(row['count']):4d} "
            f"({row['percentage']:.1f}%)"
        )

    print(
        "\nTop 10 highest-risk components:"
    )

    display_columns = [
        "component_id",
        "batch_id",
        "device_family",
        "anomaly_score",
        "predicted_leakage_168h_uA",
        "predicted_leakage_utilization",
        "predicted_leakage_slope_uA_per_hour",
        "risk_score",
        "risk_level",
        "risk_reason",
    ]

    print(
        result[
            display_columns
        ]
        .head(10)
        .round(4)
        .to_string(index=False)
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    result.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    summary.to_csv(
        SUMMARY_FILE,
        index=False,
    )

    print(
        "\nSaved:"
    )

    print(
        f"  {OUTPUT_FILE.relative_to(PROJECT_ROOT)}"
    )

    print(
        f"  {SUMMARY_FILE.relative_to(PROJECT_ROOT)}"
    )

    print(
        "\nRisk Engine completed successfully."
    )


if __name__ == "__main__":
    main()
