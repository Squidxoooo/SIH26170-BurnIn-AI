"""Train Isolation Forest on an existing CSV. Specify numeric feature columns."""
import argparse
from pathlib import Path
import pandas as pd, joblib
from sklearn.ensemble import IsolationForest

def main():
    p=argparse.ArgumentParser(); p.add_argument("--csv",required=True)
    p.add_argument("--features",nargs="+",required=True); p.add_argument("--out",default="models/anomaly.joblib")
    a=p.parse_args(); df=pd.read_csv(a.csv)
    X=df[a.features].apply(pd.to_numeric,errors="coerce").dropna()
    model=IsolationForest(contamination=0.05,random_state=42); model.fit(X)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model":model,"features":a.features,"version":"isolation_forest_v1"},a.out)
    print({"rows":len(X),"features":a.features})
if __name__=="__main__": main()
