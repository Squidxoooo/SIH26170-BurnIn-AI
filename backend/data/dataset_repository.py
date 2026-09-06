"""Read-only access to the supplied SIH26170 serving dataset."""
from functools import lru_cache
from pathlib import Path
import pandas as pd

from backend.core.config import settings


class DatasetRepository:
    def __init__(self, dataset_dir: str | None = None):
        self.root = Path(dataset_dir or settings.dataset_dir)

    @property
    def serving_path(self) -> Path:
        return self.root / "processed" / "timeseries_serving.csv"

    @lru_cache(maxsize=1)
    def serving_data(self) -> pd.DataFrame:
        if not self.serving_path.is_file():
            raise FileNotFoundError(
                f"Serving dataset not found: {self.serving_path}. Set DATASET_DIR to the extracted SIH26170_clean_dataset folder."
            )
        return pd.read_csv(self.serving_path)

    def component(self, component_id: str) -> dict | None:
        rows = self.serving_data().query("component_id == @component_id").sort_values("time_h")
        if rows.empty:
            return None
        first = rows.iloc[0]
        return {
            "component_id": component_id,
            "batch_id": first["batch_id"],
            "device_family": first["device_family"],
            "chamber_id": first["chamber_id"],
            "burn_in_temp_C": float(first["burn_in_temp_C"]),
            "measurements": rows[["time_h", "leakage_current_uA", "propagation_delay_ns"]].to_dict(orient="records"),
            "limits": {
                "leakage_static_limit_uA": float(first["leakage_static_limit_uA"]),
                "delay_static_limit_ns": float(first["delay_static_limit_ns"]),
            },
        }

    def lot(self, lot_id: str) -> dict | None:
        data = self.serving_data()
        rows = data.query("batch_id == @lot_id")
        if rows.empty:
            return None
        components = sorted(rows["component_id"].unique().tolist())
        return {
            "lot_id": lot_id,
            "component_count": len(components),
            "device_families": sorted(rows["device_family"].unique().tolist()),
            "chambers": sorted(rows["chamber_id"].unique().tolist()),
            "component_ids": components,
        }
