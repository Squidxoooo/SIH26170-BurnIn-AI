from abc import ABC, abstractmethod
import numpy as np

class Detector(ABC):
    @abstractmethod
    def fit(self, X): ...
    @abstractmethod
    def score(self, X): ...

class IsolationForestDetector(Detector):
    def __init__(self, contamination=0.05, random_state=42):
        from sklearn.ensemble import IsolationForest
        self.model = IsolationForest(contamination=contamination, random_state=random_state)
    def fit(self, X):
        self.model.fit(X)
        return self
    def score(self, X):
        raw = -self.model.score_samples(X)
        lo, hi = np.min(raw), np.max(raw)
        score = (raw-lo)/(hi-lo) if hi > lo else np.zeros_like(raw)
        return score, self.model.predict(X) == -1
