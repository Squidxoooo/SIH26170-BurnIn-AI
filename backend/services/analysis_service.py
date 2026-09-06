from __future__ import annotations

from typing import Any

from backend.ml.sih26170_pipeline import pipeline


class AnalysisService:
    """
    Adapter between FastAPI and the trained SIH26170 ML pipeline.
    """

    def __init__(
        self,
        anomaly_service: Any = None,
        drift_predictor: Any = None,
    ) -> None:
        self.pipeline = pipeline

        # Compatibility with existing backend health checks.
        self.anomaly = anomaly_service
        self.drift = drift_predictor

    def analyze(
        self,
        component_id: str,
        lot_id: str | None,
        values: dict[str, float],
        limit: float | None = None,
    ) -> dict[str, Any]:

        payload = dict(values)

        payload["component_id"] = component_id

        if lot_id is not None:
            payload["lot_id"] = lot_id

        if limit is not None:
            payload.setdefault(
                "leakage_static_limit_uA",
                float(limit),
            )

        return self.pipeline.analyze(payload)
