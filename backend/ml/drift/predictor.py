from pathlib import Path
import joblib
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor

class DriftPredictor:
    def __init__(self):
        self.models = {}
        self.best_name = None
    def fit_compare(self, X, y):
        candidates = {
            "linear_regression": LinearRegression(),
            "random_forest": RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1)
        }
        from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
        metrics = {}
        for name, model in candidates.items():
            model.fit(X, y)
            pred = model.predict(X)
            metrics[name] = {"mae": float(mean_absolute_error(y,pred)),
                             "rmse": float(np.sqrt(mean_squared_error(y,pred))),
                             "r2": float(r2_score(y,pred))}
            self.models[name] = model
        self.best_name = min(metrics, key=lambda k: metrics[k]["mae"])
        return metrics
    def predict(self, X):
        if not self.best_name:
            raise RuntimeError("No drift model trained")
        return self.models[self.best_name].predict(X)
    def save(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"models": self.models, "best_name": self.best_name}, path)
    def load(self, path):
        obj = joblib.load(path)
        self.models, self.best_name = obj["models"], obj["best_name"]
