import numpy as np
import pandas as pd

def engineer_features(df: pd.DataFrame, measurement_cols: list[str]) -> pd.DataFrame:
    out = df.copy()
    nums = out[measurement_cols].apply(pd.to_numeric, errors="coerce")
    if len(measurement_cols) >= 2:
        for a, b in zip(measurement_cols[:-1], measurement_cols[1:]):
            out[f"delta_{a}_{b}"] = nums[b] - nums[a]
            out[f"rate_{a}_{b}"] = (nums[b] - nums[a]) / np.where(nums[a].abs() < 1e-12, np.nan, nums[a].abs())
    if measurement_cols:
        x = np.arange(len(measurement_cols), dtype=float)
        vals = nums.to_numpy(float)
        out["slope"] = np.polyfit(x, np.nan_to_num(vals, nan=np.nanmedian(vals, axis=0)), 1)[0] if len(out) else 0.0
        out["max_deviation"] = nums.max(axis=1) - nums.min(axis=1)
        out["cumulative_drift"] = nums.iloc[:, -1] - nums.iloc[:, 0]
        out["volatility"] = nums.diff(axis=1).std(axis=1).fillna(0)
        lot_mean = nums.mean(axis=0).mean()
        lot_std = nums.stack().std()
        last = nums.iloc[:, -1]
        out["lot_mean"] = lot_mean
        out["lot_std"] = lot_std
        out["z_score"] = (last - lot_mean) / (lot_std if lot_std > 0 else 1.0)
        out["ratio_to_lot_mean"] = last / (lot_mean if abs(lot_mean) > 1e-12 else 1.0)
    return out.replace([np.inf, -np.inf], np.nan)
