from pathlib import Path
import pandas as pd
from backend.data.validator import validate_dataframe

def load_csv(path: str):
    p = Path(path)
    if p.suffix.lower() != ".csv":
        raise ValueError("Only CSV ingestion is supported initially")
    df = pd.read_csv(p)
    return df, validate_dataframe(df)
