from dataclasses import dataclass
from typing import List
import pandas as pd

@dataclass
class ValidationReport:
    valid: bool
    errors: List[dict]
    warnings: List[str]

def validate_dataframe(df: pd.DataFrame) -> ValidationReport:
    errors, warnings = [], []
    if df.empty:
        errors.append({"reason": "Dataset is empty"})
        return ValidationReport(False, errors, warnings)
    if df.columns.duplicated().any():
        errors.append({"reason": "Duplicate column names", "columns": df.columns[df.columns.duplicated()].tolist()})
    if df.duplicated().any():
        warnings.append(f"{int(df.duplicated().sum())} duplicate rows detected")
    for c in df.columns:
        if df[c].isna().any():
            warnings.append(f"{c}: {int(df[c].isna().sum())} missing values")
    return ValidationReport(not errors, errors, warnings)
