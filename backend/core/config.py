import os
from dataclasses import dataclass
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]

@dataclass(frozen=True)
class Settings:
    model_dir: str = os.getenv("MODEL_DIR", "models")
    # This default matches the folder extracted from SIH26170_clean_dataset.zip.
    # Override DATASET_DIR when deploying the backend elsewhere.
    dataset_dir: str = os.getenv("DATASET_DIR", str(_PROJECT_ROOT / "SIH26170_clean_dataset"))
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./burnin.db")
    max_upload_mb: int = int(os.getenv("MAX_UPLOAD_MB", "25"))
    anomaly_contamination: float = float(os.getenv("ANOMALY_CONTAMINATION", "0.05"))
    risk_watch: float = float(os.getenv("RISK_WATCH", "35"))
    risk_high: float = float(os.getenv("RISK_HIGH", "65"))
    risk_critical: float = float(os.getenv("RISK_CRITICAL", "85"))

settings = Settings()
