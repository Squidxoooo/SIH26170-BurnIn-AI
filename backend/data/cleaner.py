import pandas as pd

def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [str(c).strip() for c in out.columns]
    for c in out.select_dtypes(include="object").columns:
        out[c] = out[c].map(lambda x: x.strip() if isinstance(x, str) else x)
    return out
