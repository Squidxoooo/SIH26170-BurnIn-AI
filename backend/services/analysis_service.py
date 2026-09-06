import numpy as np
from pathlib import Path
from app.core.config import settings
from app.ml.drift.predictor import DriftPredictor
from app.services.anomaly_service import AnomalyService
from app.risk.decision import static_limit_check
from app.risk.scoring import calculate_risk
from app.services.explanation_service import explain

class AnalysisService:
    def __init__(self, anomaly_service=None, drift_predictor=None):
        model_dir = Path(settings.model_dir)
        self.anomaly = anomaly_service
        self.drift = drift_predictor
        self.anomaly_features = []
        if self.anomaly is None and (model_dir / "anomaly.joblib").is_file():
            self.anomaly = AnomalyService()
            self.anomaly_features = self.anomaly.load(model_dir / "anomaly.joblib")
        if self.drift is None and (model_dir / "drift_leakage.joblib").is_file():
            self.drift = DriftPredictor()
            self.drift.load(model_dir / "drift_leakage.joblib")

    def analyze(self, component_id, lot_id, values, limit=None):
        names = self.anomaly_features if self.anomaly_features and all(k in values for k in self.anomaly_features) else list(values)
        nums = np.array([float(values[k]) for k in names], dtype=float)
        last = nums[-1]
        static = static_limit_check(last, limit)
        X = nums.reshape(1,-1)
        if self.anomaly:
            score, flag, conf = self.anomaly.predict(X)
            anomaly_score, is_anomaly, confidence = float(score[0]), bool(flag[0]), float(conf[0])
        else:
            anomaly_score, is_anomaly, confidence = 0.0, False, 0.0
        drift_rate = float((nums[-1]-nums[0])/(abs(nums[0]) if abs(nums[0])>1e-12 else 1.0))
        predicted = None
        if self.drift and len(nums) >= 2:
            try: predicted = float(self.drift.predict(np.array([[nums[0], nums[1]]]))[0])
            except Exception: predicted = None
        violation = bool(limit is not None and predicted is not None and predicted > limit)
        z = 0.0
        risk = calculate_risk(static["status"]=="FAIL", anomaly_score, violation, drift_rate, z, confidence)
        reasons = explain(static, anomaly_score, z, drift_rate, violation)
        return {
            "component_id": component_id, "lot_id": lot_id,
            "static_check": static,
            "anomaly_analysis": {"is_anomaly": is_anomaly, "score": round(anomaly_score,4), "confidence": round(confidence,4), "detector":"IsolationForest"},
            "drift_prediction": {"prediction_mode":"EARLY" if len(nums)>=2 else "UNAVAILABLE", "predicted_168h":predicted},
            "drift_analysis": {"drift_rate":round(drift_rate,6), "predicted_limit_violation":violation},
            "risk": risk, "decision": risk["decision"], "explanation": reasons,
            "model_metadata":{"anomaly_model":"isolation_forest_v1","drift_model":"best_validated_model","feature_version":"1.0"}
        }
