from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# SIH26170 — Module B Prediction Validation
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

PREDICTION_FILE = (
    PROJECT_ROOT
    / "reports"
    / "prediction"
    / "module_b_test_predictions.csv"
)

REPORT_DIR = (
    PROJECT_ROOT
    / "reports"
    / "prediction"
)

REPORT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ------------------------------------------------------------
# Load predictions
# ------------------------------------------------------------

def load_predictions():

    if not PREDICTION_FILE.exists():
        raise FileNotFoundError(
            f"Prediction file not found:\n{PREDICTION_FILE}"
        )

    df = pd.read_csv(
        PREDICTION_FILE
    )

    required = [
        "component_id",
        "batch_id",
        "device_family",
        "leakage_168h_uA",
        "predicted_leakage_168h_uA",
        "propagation_delay_168h_ns",
        "predicted_delay_168h_ns",
        "leakage_prediction_error_uA",
        "delay_prediction_error_ns",
    ]

    missing = sorted(
        set(required) - set(df.columns)
    )

    if missing:
        raise ValueError(
            "Missing prediction columns:\n"
            + "\n".join(
                f"  - {column}"
                for column in missing
            )
        )

    return df


# ------------------------------------------------------------
# Metrics
# ------------------------------------------------------------

def calculate_metrics(df):

    leakage_error = (
        df["predicted_leakage_168h_uA"]
        - df["leakage_168h_uA"]
    )

    delay_error = (
        df["predicted_delay_168h_ns"]
        - df["propagation_delay_168h_ns"]
    )

    leakage_mae = leakage_error.abs().mean()
    delay_mae = delay_error.abs().mean()

    leakage_rmse = np.sqrt(
        np.mean(
            leakage_error ** 2
        )
    )

    delay_rmse = np.sqrt(
        np.mean(
            delay_error ** 2
        )
    )

    print("\n" + "=" * 60)
    print("MODULE B — FINAL VALIDATION")
    print("=" * 60)

    print(
        f"Test components : {len(df):,}"
    )

    print(
        f"\nLeakage prediction"
    )

    print(
        f"  MAE  : {leakage_mae:.4f} µA"
    )

    print(
        f"  RMSE : {leakage_rmse:.4f} µA"
    )

    print(
        f"\nPropagation-delay prediction"
    )

    print(
        f"  MAE  : {delay_mae:.4f} ns"
    )

    print(
        f"  RMSE : {delay_rmse:.4f} ns"
    )

    return {
        "test_components": len(df),
        "leakage_mae_uA": leakage_mae,
        "leakage_rmse_uA": leakage_rmse,
        "delay_mae_ns": delay_mae,
        "delay_rmse_ns": delay_rmse,
    }


# ------------------------------------------------------------
# Prediction-vs-actual plots
# ------------------------------------------------------------

def plot_prediction_vs_actual(
    df,
    actual_column,
    predicted_column,
    title,
    xlabel,
    output_name,
):

    actual = df[actual_column]
    predicted = df[predicted_column]

    minimum = min(
        actual.min(),
        predicted.min(),
    )

    maximum = max(
        actual.max(),
        predicted.max(),
    )

    plt.figure(
        figsize=(8, 7)
    )

    plt.scatter(
        actual,
        predicted,
        alpha=0.35,
        s=18,
    )

    plt.plot(
        [minimum, maximum],
        [minimum, maximum],
        linestyle="--",
        linewidth=2,
    )

    plt.xlabel(xlabel)
    plt.ylabel(
        "Predicted value"
    )

    plt.title(title)

    plt.grid(
        alpha=0.25
    )

    plt.tight_layout()

    plt.savefig(
        REPORT_DIR / output_name,
        dpi=160,
    )

    plt.close()


# ------------------------------------------------------------
# Error distribution plots
# ------------------------------------------------------------

def plot_error_distribution(
    df,
    error_column,
    title,
    xlabel,
    output_name,
):

    plt.figure(
        figsize=(9, 6)
    )

    plt.hist(
        df[error_column].dropna(),
        bins=40,
        alpha=0.75,
    )

    plt.axvline(
        0,
        linestyle="--",
        linewidth=2,
    )

    plt.xlabel(xlabel)
    plt.ylabel(
        "Number of components"
    )

    plt.title(title)

    plt.grid(
        alpha=0.25
    )

    plt.tight_layout()

    plt.savefig(
        REPORT_DIR / output_name,
        dpi=160,
    )

    plt.close()


# ------------------------------------------------------------
# Device-family analysis
# ------------------------------------------------------------

def analyze_device_families(df):

    rows = []

    print("\n" + "=" * 60)
    print("PERFORMANCE BY DEVICE FAMILY")
    print("=" * 60)

    for family, group in (
        df.groupby("device_family")
    ):

        leakage_mae = (
            group[
                "leakage_prediction_error_uA"
            ]
            .abs()
            .mean()
        )

        delay_mae = (
            group[
                "delay_prediction_error_ns"
            ]
            .abs()
            .mean()
        )

        rows.append({
            "device_family": family,
            "components": len(group),
            "leakage_mae_uA": leakage_mae,
            "delay_mae_ns": delay_mae,
        })

        print(
            f"\n{family}"
        )

        print(
            f"  Components : {len(group):,}"
        )

        print(
            f"  Leakage MAE: {leakage_mae:.4f} µA"
        )

        print(
            f"  Delay MAE  : {delay_mae:.4f} ns"
        )

    result = pd.DataFrame(
        rows
    )

    result.to_csv(
        REPORT_DIR
        / "module_b_by_device_family.csv",
        index=False,
    )

    return result


# ------------------------------------------------------------
# Largest prediction errors
# ------------------------------------------------------------

def show_largest_errors(df):

    result = df.copy()

    result["absolute_leakage_error"] = (
        result[
            "leakage_prediction_error_uA"
        ].abs()
    )

    result = result.sort_values(
        "absolute_leakage_error",
        ascending=False,
    )

    columns = [
        "component_id",
        "batch_id",
        "device_family",
        "leakage_168h_uA",
        "predicted_leakage_168h_uA",
        "leakage_prediction_error_uA",
        "propagation_delay_168h_ns",
        "predicted_delay_168h_ns",
        "delay_prediction_error_ns",
    ]

    print("\n" + "=" * 60)
    print("LARGEST LEAKAGE PREDICTION ERRORS")
    print("=" * 60)

    print(
        result[columns]
        .head(15)
        .round(4)
        .to_string(index=False)
    )


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main():

    df = load_predictions()

    metrics = calculate_metrics(
        df
    )

    # Prediction plots.
    plot_prediction_vs_actual(
        df,
        "leakage_168h_uA",
        "predicted_leakage_168h_uA",
        "Actual vs predicted 168h leakage",
        "Actual leakage (µA)",
        "module_b_leakage_prediction.png",
    )

    plot_prediction_vs_actual(
        df,
        "propagation_delay_168h_ns",
        "predicted_delay_168h_ns",
        "Actual vs predicted 168h propagation delay",
        "Actual delay (ns)",
        "module_b_delay_prediction.png",
    )

    # Error distributions.
    plot_error_distribution(
        df,
        "leakage_prediction_error_uA",
        "Leakage prediction error distribution",
        "Prediction error (µA)",
        "module_b_leakage_error.png",
    )

    plot_error_distribution(
        df,
        "delay_prediction_error_ns",
        "Delay prediction error distribution",
        "Prediction error (ns)",
        "module_b_delay_error.png",
    )

    # Device-family performance.
    analyze_device_families(
        df
    )

    # Largest errors.
    show_largest_errors(
        df
    )

    # Save summary.
    pd.Series(
        metrics
    ).to_csv(
        REPORT_DIR
        / "module_b_validation_summary.csv",
        header=["value"],
    )

    print("\nGenerated validation reports:")
    print(
        "  reports/prediction/module_b_validation_summary.csv"
    )
    print(
        "  reports/prediction/module_b_by_device_family.csv"
    )
    print(
        "  reports/prediction/module_b_leakage_prediction.png"
    )
    print(
        "  reports/prediction/module_b_delay_prediction.png"
    )
    print(
        "  reports/prediction/module_b_leakage_error.png"
    )
    print(
        "  reports/prediction/module_b_delay_error.png"
    )

    print(
        "\nModule B validation completed successfully."
    )


if __name__ == "__main__":
    main()
