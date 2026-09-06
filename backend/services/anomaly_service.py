import numpy as np
import joblib
from app.ml.anomaly.detector import IsolationForestDetector

class AnomalyService:
    def __init__(self):
        self.detector = None
    def train(self, X, contamination=0.05):
        self.detector = IsolationForestDetector(contamination=contamination).fit(X)

    def load(self, path):
        artifact = joblib.load(path)
        detector = IsolationForestDetector()
        detector.model = artifact["model"]
        self.detector = detector
        return artifact.get("features", [])
    def predict(self, X):
        if self.detector is None:
            raise RuntimeError("Anomaly model is not loaded")
        score, flags = self.detector.score(X)
        confidence = np.clip(np.abs(score-.5)*2, 0, 1)
        return score, flags, confidence
