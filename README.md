# SIH26170 Clean Dataset

This package is the cleaned/structured data layer for the SIH26170 prototype.

## Source data
- `raw/components_raw.csv` — untouched wide-format component measurements.
- `raw/timeseries_raw.csv` — untouched long-format measurements (0h/24h/96h/168h).
- `raw/batch_metadata.csv` — batch/chamber/environment metadata.
- `reference/data_dictionary.csv` — original data dictionary.

## ML-ready datasets
- `processed/module_a_early_screening.csv` — only information available by 24h for peer-based anomaly detection.
- `processed/module_b_regression.csv` — 0h/24h inputs and 168h targets, with a grouped train/test split.
- `processed/evaluation_labels.csv` — benchmark labels; never use these as model inputs.
- `processed/timeseries_serving.csv` — clean time-series data for backend/demo visualization without benchmark labels.

## Important anti-leakage rules
1. Never use `behavior_type`, `ground_truth_status`, or `static_screen_fail` as model features.
2. Never use 96h/168h measurements as inputs to a model that predicts 168h.
3. Never use 168h-derived slopes or 168h peer statistics for early screening.
4. Split by `batch_id`, not random rows.
5. Do not claim the synthetic labels/data are real ISRO telemetry.
6. The safety slope is intentionally configurable and is NOT presented as an official ISRO threshold.

## Current grouped split
Test batches: B09, B10, B11, B20.
They cover MixedSignal, Analog, Logic, and Memory device families.
