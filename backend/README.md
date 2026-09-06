# AI-Driven Burn-In & ESS Screening Backend

A modular FastAPI backend for anomaly detection, early 168h prediction, drift analysis,
risk scoring and explainable screening.

## Important
This repository does **not** create or fabricate a dataset. Training requires your
existing burn-in/ESS CSV.

## Run
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Swagger: `/docs`

## Train
First inspect the real CSV columns and choose the actual 0h, 24h and 168h columns:
```bash
python training/train_drift.py --csv path/to/your.csv --x0 value_0h --x24 value_24h --y168 value_168h
python training/train_anomaly.py --csv path/to/your.csv --features value_0h value_24h
```

Do not assume these names exist in your dataset. The prompt requires inspection of
actual identifiers, units, intervals, labels and missing-value patterns before final
mapping.

## Included SIH26170 dataset

The extracted project is preconfigured to use the sibling
`../SIH26170_clean_dataset` directory. The REST endpoints use the leak-free
`processed/timeseries_serving.csv` file:

- `GET /api/v1/components/C000001` returns its time-series measurements and limits.
- `GET /api/v1/lots/B01` returns its component summary.

Train from the processed files after installing dependencies. These commands keep
the documented 0h/24h-to-168h mapping and do not use benchmark labels as inputs:

```bash
python training/train_anomaly.py --csv ../SIH26170_clean_dataset/processed/module_a_early_screening.csv --features leakage_0h_uA leakage_24h_uA propagation_delay_0h_ns propagation_delay_24h_ns --out models/anomaly.joblib
python training/train_drift.py --csv ../SIH26170_clean_dataset/processed/module_b_regression.csv --x0 leakage_0h_uA --x24 leakage_24h_uA --y168 leakage_168h_uA --out models/drift_leakage.joblib
```

## Architecture
- `app/data`: ingestion, validation, cleaning, deterministic feature engineering
- `app/ml`: replaceable anomaly/drift model implementations
- `app/risk`: deterministic engineering decision layer
- `app/services`: orchestration
- `app/api`: versioned REST interface
- `training`: training only; never retrain on an API request
- `tests`: pytest tests

## API
- GET `/api/v1/health`
- POST `/api/v1/analyze/component`
- POST `/api/v1/anomaly/detect`
- POST `/api/v1/prediction/drift`
- GET `/api/v1/components/{component_id}`
- GET `/api/v1/lots/{lot_id}`

## Production hardening still required
The exact dataset schema must be inspected before final feature mapping. The anomaly
model should be trained/evaluated using available outcome labels or validated
engineering proxies; the drift model should use temporal/group-aware validation
rather than training-set metrics for final model selection. Add persistence,
upload handling, SHAP, lot analytics and batch endpoints after the schema is known.
