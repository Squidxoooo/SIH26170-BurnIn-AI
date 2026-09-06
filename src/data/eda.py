from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# SIH26170 — Exploratory Data Analysis
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_FILE = PROJECT_ROOT / "data" / "raw" / "components_raw.csv"
FEATURE_FILE = PROJECT_ROOT / "data" / "processed" / "module_a_features.csv"

REPORT_DIR = PROJECT_ROOT / "reports" / "eda"
REPORT_DIR.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# Load data
# ------------------------------------------------------------

print("Loading dataset...")

df = pd.read_csv(RAW_FILE)

print(
    f"Loaded {len(df):,} components "
    f"with {len(df.columns)} columns."
)


# ------------------------------------------------------------
# Basic data quality
# ------------------------------------------------------------

print("\n" + "=" * 60)
print("DATA QUALITY")
print("=" * 60)

print(f"Rows       : {len(df):,}")
print(f"Columns    : {len(df.columns)}")
print(f"Duplicates : {df['component_id'].duplicated().sum():,}")
print(f"Missing values: {df.isna().sum().sum():,}")


missing = (
    df.isna()
    .sum()
    .sort_values(ascending=False)
)

missing = missing[missing > 0]

print("\nColumns containing missing values:")

if len(missing):
    print(missing.to_string())
else:
    print("None")


# ------------------------------------------------------------
# Dataset composition
# ------------------------------------------------------------

print("\n" + "=" * 60)
print("DATASET COMPOSITION")
print("=" * 60)

print("\nDevice families:")

print(
    df["device_family"]
    .value_counts()
    .to_string()
)


print("\nGround truth:")

print(
    df["ground_truth_status"]
    .value_counts()
    .to_string()
)


print("\nBehavior types:")

print(
    df["behavior_type"]
    .value_counts()
    .to_string()
)


# ------------------------------------------------------------
# Static screening analysis
# ------------------------------------------------------------

print("\n" + "=" * 60)
print("STATIC SCREEN ANALYSIS")
print("=" * 60)

static_failures = int(
    df["static_screen_fail"]
    .fillna(False)
    .sum()
)

defective = df["ground_truth_status"] == "Defective"

defective_count = int(defective.sum())

latent = df[
    defective
    & (~df["static_screen_fail"].fillna(False))
].copy()

print(f"Total defective components       : {defective_count:,}")
print(f"Static-screen failures           : {static_failures:,}")
print(
    f"Defective components missed by "
    f"static screen                    : {len(latent):,}"
)

if defective_count:
    latent_rate = len(latent) / defective_count * 100

    print(
        f"Static-screen miss rate among "
        f"defective components            : {latent_rate:.2f}%"
    )


# ------------------------------------------------------------
# Measurement statistics
# ------------------------------------------------------------

measurement_columns = [
    "leakage_0h_uA",
    "leakage_24h_uA",
    "leakage_96h_uA",
    "leakage_168h_uA",
    "propagation_delay_0h_ns",
    "propagation_delay_24h_ns",
    "propagation_delay_96h_ns",
    "propagation_delay_168h_ns",
]

print("\n" + "=" * 60)
print("MEASUREMENT STATISTICS")
print("=" * 60)

print(
    df[measurement_columns]
    .describe()
    .round(3)
    .to_string()
)


# ------------------------------------------------------------
# Static limit margins
# ------------------------------------------------------------

df["leakage_margin_168h_uA"] = (
    df["leakage_static_limit_uA"]
    - df["leakage_168h_uA"]
)

df["delay_margin_168h_ns"] = (
    df["delay_static_limit_ns"]
    - df["propagation_delay_168h_ns"]
)


# ------------------------------------------------------------
# Behavior trajectory plot
# ------------------------------------------------------------

print("\nGenerating trajectory plots...")


hours = np.array([0, 24, 96, 168])


def plot_behavior_trajectory(behavior, output_name):

    subset = df[
        df["behavior_type"] == behavior
    ].copy()

    if subset.empty:
        return

    leakage = subset[
        [
            "leakage_0h_uA",
            "leakage_24h_uA",
            "leakage_96h_uA",
            "leakage_168h_uA",
        ]
    ]

    median = leakage.median()
    q25 = leakage.quantile(0.25)
    q75 = leakage.quantile(0.75)

    plt.figure(figsize=(9, 6))

    plt.plot(
        hours,
        median.values,
        marker="o",
        linewidth=2,
        label=behavior,
    )

    plt.fill_between(
        hours,
        q25.values,
        q75.values,
        alpha=0.2,
        label="25th–75th percentile",
    )

    plt.xlabel("Burn-in time (hours)")
    plt.ylabel("Leakage (µA)")
    plt.title(
        f"Leakage trajectory — {behavior}"
    )

    plt.grid(alpha=0.25)
    plt.legend()
    plt.tight_layout()

    plt.savefig(
        REPORT_DIR / output_name,
        dpi=160,
    )

    plt.close()


for behavior in [
    "Healthy",
    "GradualDrift",
    "RapidDrift",
    "NearLimitDrift",
    "SuddenAnomaly",
    "EarlyLifeInstability",
    "NonMonotonicAnomaly",
]:

    plot_behavior_trajectory(
        behavior,
        f"{behavior}_trajectory.png",
    )


# ------------------------------------------------------------
# Healthy vs defective trajectory
# ------------------------------------------------------------

print("Generating healthy vs defective plot...")


healthy = df[
    df["ground_truth_status"] == "Healthy"
]

defective_df = df[
    df["ground_truth_status"] == "Defective"
]


def median_trajectory(data):

    return data[
        [
            "leakage_0h_uA",
            "leakage_24h_uA",
            "leakage_96h_uA",
            "leakage_168h_uA",
        ]
    ].median()


healthy_median = median_trajectory(healthy)
defective_median = median_trajectory(defective_df)


plt.figure(figsize=(9, 6))

plt.plot(
    hours,
    healthy_median.values,
    marker="o",
    linewidth=2,
    label="Healthy",
)

plt.plot(
    hours,
    defective_median.values,
    marker="o",
    linewidth=2,
    label="Defective",
)

plt.xlabel("Burn-in time (hours)")
plt.ylabel("Leakage (µA)")
plt.title("Healthy vs defective leakage trajectory")

plt.grid(alpha=0.25)
plt.legend()
plt.tight_layout()

plt.savefig(
    REPORT_DIR / "healthy_vs_defective_trajectory.png",
    dpi=160,
)

plt.close()


# ------------------------------------------------------------
# Latent defect analysis
# ------------------------------------------------------------

print("\n" + "=" * 60)
print("LATENT DEFECT ANALYSIS")
print("=" * 60)

if len(latent):

    print("\nExample latent defects:")

    example_columns = [
        "component_id",
        "batch_id",
        "device_family",
        "behavior_type",
        "leakage_0h_uA",
        "leakage_24h_uA",
        "leakage_96h_uA",
        "leakage_168h_uA",
        "leakage_static_limit_uA",
    ]

    print(
        latent[
            example_columns
        ]
        .head(15)
        .to_string(index=False)
    )

    latent.to_csv(
        REPORT_DIR / "latent_defects.csv",
        index=False,
    )

else:

    print(
        "No defective components passed "
        "the static screen."
    )


# ------------------------------------------------------------
# Anomaly score analysis
# ------------------------------------------------------------

if FEATURE_FILE.exists():

    print("\n" + "=" * 60)
    print("ANOMALY SIGNAL ANALYSIS")
    print("=" * 60)

    features = pd.read_csv(FEATURE_FILE)

    merged = df[
        [
            "component_id",
            "ground_truth_status",
            "static_screen_fail",
        ]
    ].merge(
        features[
            [
                "component_id",
                "anomaly_score",
                "max_early_abs_robust_z",
            ]
        ],
        on="component_id",
        how="inner",
    )

    latent_scores = merged[
        (merged["ground_truth_status"] == "Defective")
        & (~merged["static_screen_fail"].fillna(False))
    ]

    healthy_scores = merged[
        merged["ground_truth_status"] == "Healthy"
    ]

    print(
        f"Healthy components analyzed : "
        f"{len(healthy_scores):,}"
    )

    print(
        f"Latent defects analyzed     : "
        f"{len(latent_scores):,}"
    )

    if len(healthy_scores):

        print(
            "\nHealthy anomaly score:"
        )

        print(
            healthy_scores["anomaly_score"]
            .describe()
            .round(4)
            .to_string()
        )

    if len(latent_scores):

        print(
            "\nLatent-defect anomaly score:"
        )

        print(
            latent_scores["anomaly_score"]
            .describe()
            .round(4)
            .to_string()
        )

    # Score distribution.
    plt.figure(figsize=(9, 6))

    plt.hist(
        healthy_scores["anomaly_score"].dropna(),
        bins=30,
        alpha=0.6,
        label="Healthy",
    )

    if len(latent_scores):

        plt.hist(
            latent_scores["anomaly_score"].dropna(),
            bins=30,
            alpha=0.6,
            label="Latent defects",
        )

    plt.xlabel("Anomaly score")
    plt.ylabel("Number of components")
    plt.title(
        "Early anomaly score distribution"
    )

    plt.grid(alpha=0.25)
    plt.legend()
    plt.tight_layout()

    plt.savefig(
        REPORT_DIR / "anomaly_score_distribution.png",
        dpi=160,
    )

    plt.close()

else:

    print(
        "\nModule A feature file not found."
    )


# ------------------------------------------------------------
# Batch analysis
# ------------------------------------------------------------

print("\n" + "=" * 60)
print("BATCH ANALYSIS")
print("=" * 60)

batch_summary = (
    df.groupby("batch_id")
    .agg(
        components=("component_id", "count"),
        defective=(
            "ground_truth_status",
            lambda x: (x == "Defective").sum(),
        ),
        static_failures=(
            "static_screen_fail",
            "sum",
        ),
        mean_leakage_168h=(
            "leakage_168h_uA",
            "mean",
        ),
    )
    .round(3)
)

print(
    batch_summary.to_string()
)

batch_summary.to_csv(
    REPORT_DIR / "batch_summary.csv"
)


# ------------------------------------------------------------
# Final report
# ------------------------------------------------------------

summary = {
    "total_components": len(df),
    "total_columns": len(df.columns),
    "duplicate_components": int(
        df["component_id"].duplicated().sum()
    ),
    "missing_values": int(
        df.isna().sum().sum()
    ),
    "healthy_components": int(
        (df["ground_truth_status"] == "Healthy").sum()
    ),
    "defective_components": int(
        (df["ground_truth_status"] == "Defective").sum()
    ),
    "static_screen_failures": static_failures,
    "latent_defects": len(latent),
}


pd.Series(summary).to_csv(
    REPORT_DIR / "eda_summary.csv",
    header=["value"],
)


print("\n" + "=" * 60)
print("EDA COMPLETE")
print("=" * 60)

print("\nSummary:")

for key, value in summary.items():

    print(
        f"{key:30s}: {value:,}"
    )

print("\nReports saved to:")

print(REPORT_DIR)

print("\nGenerated files:")

for file in sorted(REPORT_DIR.iterdir()):

    if file.is_file():

        print(f"  {file.name}")
