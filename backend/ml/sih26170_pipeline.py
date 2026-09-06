from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

MODULE_A_MODEL = PROJECT_ROOT / "models" / "module_a_isolation_forest.joblib"
MODULE_A_CALIBRATION = PROJECT_ROOT / "models" / "module_a_score_calibration.json"
MODULE_B_MODEL = PROJECT_ROOT / "models" / "module_b_final_model.joblib"
RISK_POLICY = PROJECT_ROOT / "config" / "model_rules.json"

RAW_COMPONENTS = PROJECT_ROOT / "data" / "raw" / "components_raw.csv"


MODULE_A_FEATURES = [
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

MODULE_B_FEATURES = [
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
    "leakage_limit_margin_24h_uA",
    "delay_limit_margin_24h_ns",
    "leakage_limit_utilization_24h",
    "delay_limit_utilization_24h",
    "leakage_change_to_baseline_ratio",
    "delay_change_to_baseline_ratio",
    "max_abs_peer_z",
    "max_abs_change_z",
    "device_family",
    "chamber_id",
]


def _float(value: Any, default: float = 0.0) -> float:
    try:
        value = float(value)
        return value if np.isfinite(value) else default
    except (TypeError, ValueError):
        return default


def _safe_ratio(a: float, b: float) -> float:
    return a / b if abs(b) > 1e-12 else 0.0


def _relative_change(start: float, end: float) -> float:
    return (end - start) / abs(start) if abs(start) > 1e-12 else 0.0


def _robust_z(value: float, series: pd.Series) -> float:
    values = pd.to_numeric(series, errors="coerce").dropna()

    if values.empty:
        return 0.0

    median = float(values.median())
    mad = float(np.median(np.abs(values.to_numpy() - median)))

    if mad <= 1e-12:
        return 0.0

    return float(0.6745 * (value - median) / mad)


def _peer_statistics(
    payload: dict[str, Any],
) -> dict[str, float]:
    """
    Reproduce the training peer definition:
        batch_id + device_family

    The training pipeline uses robust median/MAD z-scores.
    """

    batch_id = str(
        payload.get("batch_id", payload.get("lot_id", "UNKNOWN"))
    )

    device_family = str(
        payload.get("device_family", "Unknown")
    )

    leakage_0 = _float(payload.get("leakage_0h_uA"))
    leakage_24 = _float(payload.get("leakage_24h_uA"))
    delay_0 = _float(payload.get("propagation_delay_0h_ns"))
    delay_24 = _float(payload.get("propagation_delay_24h_ns"))

    leakage_delta = leakage_24 - leakage_0
    delay_delta = delay_24 - delay_0

    if not RAW_COMPONENTS.is_file():
        return {
            "leakage_peer_z_0h": 0.0,
            "leakage_peer_z_24h": 0.0,
            "delay_peer_z_0h": 0.0,
            "delay_peer_z_24h": 0.0,
            "leakage_peer_z_change": 0.0,
            "delay_peer_z_change": 0.0,
        }

    df = pd.read_csv(RAW_COMPONENTS)

    required = {
        "batch_id",
        "device_family",
        "leakage_0h_uA",
        "leakage_24h_uA",
        "propagation_delay_0h_ns",
        "propagation_delay_24h_ns",
    }

    if not required.issubset(df.columns):
        raise ValueError(
            "components_raw.csv is missing required peer columns."
        )

    peers = df[
        (df["batch_id"].astype(str) == batch_id)
        & (df["device_family"].astype(str) == device_family)
    ].copy()

    # For a new/live component, include the incoming observation
    # in the peer set. This mirrors the training transform where
    # each component belongs to its own peer group.
    live_row = pd.DataFrame(
        [{
            "batch_id": batch_id,
            "device_family": device_family,
            "leakage_0h_uA": leakage_0,
            "leakage_24h_uA": leakage_24,
            "propagation_delay_0h_ns": delay_0,
            "propagation_delay_24h_ns": delay_24,
        }]
    )

    peers = pd.concat(
        [peers, live_row],
        ignore_index=True,
    )

    peers["leakage_delta_0_24"] = (
        pd.to_numeric(peers["leakage_24h_uA"], errors="coerce")
        - pd.to_numeric(peers["leakage_0h_uA"], errors="coerce")
    )

    peers["delay_delta_0_24"] = (
        pd.to_numeric(peers["propagation_delay_24h_ns"], errors="coerce")
        - pd.to_numeric(peers["propagation_delay_0h_ns"], errors="coerce")
    )

    return {
        "leakage_peer_z_0h": _robust_z(
            leakage_0,
            peers["leakage_0h_uA"],
        ),
        "leakage_peer_z_24h": _robust_z(
            leakage_24,
            peers["leakage_24h_uA"],
        ),
        "delay_peer_z_0h": _robust_z(
            delay_0,
            peers["propagation_delay_0h_ns"],
        ),
        "delay_peer_z_24h": _robust_z(
            delay_24,
            peers["propagation_delay_24h_ns"],
        ),
        "leakage_peer_z_change": _robust_z(
            leakage_delta,
            peers["leakage_delta_0_24"],
        ),
        "delay_peer_z_change": _robust_z(
            delay_delta,
            peers["delay_delta_0_24"],
        ),
    }


def _build_features(
    payload: dict[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame]:

    ambient = _float(payload.get("ambient_temp_C"))
    burn_in = _float(payload.get("burn_in_temp_C"))
    humidity = _float(payload.get("humidity_pct"))

    leakage_0 = _float(payload.get("leakage_0h_uA"))
    leakage_24 = _float(payload.get("leakage_24h_uA"))

    delay_0 = _float(payload.get("propagation_delay_0h_ns"))
    delay_24 = _float(payload.get("propagation_delay_24h_ns"))

    leakage_limit = _float(
        payload.get("leakage_static_limit_uA"),
        50.0,
    )

    delay_limit = _float(
        payload.get("delay_static_limit_ns"),
        12.0,
    )

    leakage_delta = leakage_24 - leakage_0
    delay_delta = delay_24 - delay_0

    leakage_rel = _relative_change(
        leakage_0,
        leakage_24,
    )

    delay_rel = _relative_change(
        delay_0,
        delay_24,
    )

    leakage_slope = leakage_delta / 24.0
    delay_slope = delay_delta / 24.0

    peer = _peer_statistics(payload)

    max_abs_peer_z = max(
        abs(peer["leakage_peer_z_0h"]),
        abs(peer["leakage_peer_z_24h"]),
        abs(peer["delay_peer_z_0h"]),
        abs(peer["delay_peer_z_24h"]),
        abs(peer["leakage_peer_z_change"]),
        abs(peer["delay_peer_z_change"]),
    )

    max_abs_early_z = max(
        abs(peer["leakage_peer_z_0h"]),
        abs(peer["leakage_peer_z_24h"]),
        abs(peer["delay_peer_z_0h"]),
        abs(peer["delay_peer_z_24h"]),
    )

    max_abs_change_z = max(
        abs(peer["leakage_peer_z_change"]),
        abs(peer["delay_peer_z_change"]),
    )

    row = {
        "ambient_temp_C": ambient,
        "burn_in_temp_C": burn_in,
        "humidity_pct": humidity,
        "leakage_0h_uA": leakage_0,
        "leakage_24h_uA": leakage_24,
        "propagation_delay_0h_ns": delay_0,
        "propagation_delay_24h_ns": delay_24,
        "leakage_delta_0_24": leakage_delta,
        "delay_delta_0_24": delay_delta,
        "leakage_relative_change_0_24": leakage_rel,
        "delay_relative_change_0_24": delay_rel,
        "leakage_early_slope_uA_per_hour": leakage_slope,
        "delay_early_slope_ns_per_hour": delay_slope,
        "leakage_peer_z_0h": peer["leakage_peer_z_0h"],
        "leakage_peer_z_24h": peer["leakage_peer_z_24h"],
        "delay_peer_z_0h": peer["delay_peer_z_0h"],
        "delay_peer_z_24h": peer["delay_peer_z_24h"],
        "leakage_peer_z_change": peer["leakage_peer_z_change"],
        "delay_peer_z_change": peer["delay_peer_z_change"],
        "leakage_change_to_baseline_ratio": _safe_ratio(
            leakage_24,
            leakage_0,
        ),
        "delay_change_to_baseline_ratio": _safe_ratio(
            delay_24,
            delay_0,
        ),
        "leakage_limit_margin_24h_uA": leakage_limit - leakage_24,
        "delay_limit_margin_24h_ns": delay_limit - delay_24,
        "leakage_limit_utilization_24h": _safe_ratio(
            leakage_24,
            leakage_limit,
        ),
        "delay_limit_utilization_24h": _safe_ratio(
            delay_24,
            delay_limit,
        ),
        "max_abs_peer_z": max_abs_peer_z,
        "max_abs_early_z": max_abs_early_z,
        "max_abs_change_z": max_abs_change_z,
        "device_family": str(
            payload.get("device_family", "Unknown")
        ),
        "chamber_id": str(
            payload.get("chamber_id", "Unknown")
        ),
    }

    a = pd.DataFrame(
        [{k: row[k] for k in MODULE_A_FEATURES}],
        columns=MODULE_A_FEATURES,
    )

    b = pd.DataFrame(
        [{k: row[k] for k in MODULE_B_FEATURES}],
        columns=MODULE_B_FEATURES,
    )

    return a, b


def _load() -> tuple[Any, Any, dict[str, Any], dict[str, Any]]:
    for path in [
        MODULE_A_MODEL,
        MODULE_A_CALIBRATION,
        MODULE_B_MODEL,
        RISK_POLICY,
    ]:
        if not path.is_file():
            raise FileNotFoundError(str(path))

    module_a = joblib.load(MODULE_A_MODEL)
    module_b = joblib.load(MODULE_B_MODEL)

    with MODULE_A_CALIBRATION.open() as f:
        calibration = json.load(f)

    with RISK_POLICY.open() as f:
        policy = json.load(f)

    return module_a, module_b, calibration, policy


def _risk(
    anomaly_score: float,
    predicted_leakage: float,
    predicted_slope: float,
    predicted_delay: float,
    leakage_limit: float,
    delay_limit: float,
    policy: dict[str, Any],
) -> tuple[float, str, str, list[str]]:

    leakage_utilization = _safe_ratio(
        predicted_leakage,
        leakage_limit,
    )

    delay_utilization = _safe_ratio(
        predicted_delay,
        delay_limit,
    )

    anomaly_watch = float(policy["anomaly_watch"])
    anomaly_high = float(policy["anomaly_high"])

    leakage_watch = float(
        policy["leakage_utilization_watch"]
    )
    leakage_high = float(
        policy["leakage_utilization_high"]
    )

    slope_watch = float(
        policy["leakage_slope_watch_uA_per_hour"]
    )
    slope_high = float(
        policy["leakage_slope_high_uA_per_hour"]
    )

    reasons: list[str] = []

    anomaly_component = np.clip(
        anomaly_score,
        0.0,
        1.0,
    )

    leakage_component = np.clip(
        leakage_utilization,
        0.0,
        1.0,
    )

    slope_component = np.clip(
        _safe_ratio(
            predicted_slope,
            slope_high,
        ),
        0.0,
        1.0,
    )

    delay_component = np.clip(
        delay_utilization,
        0.0,
        1.0,
    )

    score = float(
        100.0
        * (
            0.35 * anomaly_component
            + 0.30 * leakage_component
            + 0.15 * slope_component
            + 0.20 * delay_component
        )
    )

    if anomaly_score >= anomaly_high:
        reasons.append("High early anomaly")
    elif anomaly_score >= anomaly_watch:
        reasons.append("Elevated early anomaly")

    if leakage_utilization >= leakage_high:
        reasons.append(
            "Predicted 168h leakage exceeds the configured high threshold"
        )
    elif leakage_utilization >= leakage_watch:
        reasons.append(
            "Predicted 168h leakage approaches the configured high threshold"
        )

    if predicted_slope >= slope_high:
        reasons.append(
            "Projected leakage drift exceeds the configured high threshold"
        )
    elif predicted_slope >= slope_watch:
        reasons.append(
            "Projected leakage drift is elevated"
        )

    if delay_utilization >= 1.0:
        reasons.append(
            "Predicted 168h propagation delay exceeds the static limit"
        )
    elif delay_utilization >= 0.90:
        reasons.append(
            "Predicted 168h propagation delay approaches the static limit"
        )

    high = (
        anomaly_score >= anomaly_high
        or leakage_utilization >= leakage_high
        or predicted_slope >= slope_high
        or delay_utilization >= 1.0
    )

    watch = (
        anomaly_score >= anomaly_watch
        or leakage_utilization >= leakage_watch
        or predicted_slope >= slope_watch
        or delay_utilization >= 0.90
    )

    if high:
        level = "HIGH"
        status = "RED"
    elif watch:
        level = "WATCH"
        status = "YELLOW"
    else:
        level = "NORMAL"
        status = "GREEN"

    if not reasons:
        reasons.append(
            "Early behaviour and projected trajectory remain within configured thresholds"
        )

    return score, level, status, reasons


class SIH26170Pipeline:

    def __init__(self) -> None:
        (
            self.module_a,
            self.module_b,
            self.calibration,
            self.policy,
        ) = _load()

        self.module_a_features = list(
            getattr(
                self.module_a,
                "feature_names_in_",
                MODULE_A_FEATURES,
            )
        )

        self.module_b_features = list(
            getattr(
                self.module_b,
                "feature_names_in_",
                MODULE_B_FEATURES,
            )
        )

    def analyze(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any]:

        module_a_df, module_b_df = _build_features(payload)

        if list(module_a_df.columns) != self.module_a_features:
            raise ValueError(
                "Module A feature mismatch."
            )

        if list(module_b_df.columns) != self.module_b_features:
            raise ValueError(
                "Module B feature mismatch."
            )

        # Module A
        raw_anomaly = float(
            self.module_a.decision_function(
                module_a_df
            )[0]
        )

        lo = float(self.calibration["min"])
        hi = float(self.calibration["max"])

        if abs(hi - lo) < 1e-12:
            anomaly_score = 0.0
        else:
            anomaly_score = float(
                np.clip(
                    (raw_anomaly - lo) / (hi - lo),
                    0.0,
                    1.0,
                )
            )

        # Module B
        prediction = self.module_b.predict(
            module_b_df
        )[0]

        predicted_leakage = float(prediction[0])
        predicted_delay = float(prediction[1])

        leakage_24 = _float(
            payload.get("leakage_24h_uA")
        )

        predicted_slope = (
            predicted_leakage - leakage_24
        ) / 144.0

        leakage_limit = _float(
            payload.get("leakage_static_limit_uA"),
            50.0,
        )

        delay_limit = _float(
            payload.get("delay_static_limit_ns"),
            12.0,
        )

        score, level, status, reasons = _risk(
            anomaly_score,
            predicted_leakage,
            predicted_slope,
            predicted_delay,
            leakage_limit,
            delay_limit,
            self.policy,
        )

        return {
            "component_id": payload.get(
                "component_id",
                "UNKNOWN",
            ),
            "lot_id": payload.get(
                "lot_id",
                payload.get("batch_id"),
            ),
            "static_check": {
                "leakage_24h_uA": leakage_24,
                "leakage_limit_uA": leakage_limit,
                "leakage_status": (
                    "PASS"
                    if leakage_24 <= leakage_limit
                    else "FAIL"
                ),
                "delay_24h_ns": _float(
                    payload.get(
                        "propagation_delay_24h_ns"
                    )
                ),
                "delay_limit_ns": delay_limit,
            },
            "anomaly_analysis": {
                "score": round(
                    anomaly_score,
                    4,
                ),
                "detector": "IsolationForest",
                "is_anomalous": (
                    anomaly_score
                    >= float(
                        self.policy["anomaly_watch"]
                    )
                ),
            },
            "drift_prediction": {
                "predicted_leakage_168h_uA": round(
                    predicted_leakage,
                    4,
                ),
                "predicted_delay_168h_ns": round(
                    predicted_delay,
                    4,
                ),
            },
            "drift_analysis": {
                "predicted_leakage_slope_uA_per_hour": round(
                    predicted_slope,
                    6,
                ),
            },
            "risk": {
                "score": round(score, 2),
                "level": level,
                "status": status,
            },
            "decision": level,
            "explanation": reasons,
            "model_metadata": {
                "module_a": (
                    "module_a_isolation_forest.joblib"
                ),
                "module_b": (
                    "module_b_final_model.joblib"
                ),
                "risk_policy": (
                    "config/model_rules.json"
                ),
                "peer_group": [
                    "batch_id",
                    "device_family",
                ],
                "last_observed_hour": 24,
                "prediction_horizon": 168,
            },
        }


pipeline = SIH26170Pipeline()
