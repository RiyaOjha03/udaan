"""Spatially grouped score stability for the unsupervised detector (no accuracy metrics)."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import RobustScaler
from sklearn.model_selection import GroupKFold

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "processed" / "model_features.csv"
OUT = ROOT / "outputs" / "metrics" / "spatial_score_stability.json"


def main() -> None:
    if not INPUT.exists():
        OUT.parent.mkdir(parents=True, exist_ok=True)
        result = {"status": "not_evaluated", "reason": "No complete multivariate model feature table; baseline extract contains uranium only.", "metrics": None}
        OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(json.dumps(result, indent=2))
        return
    d = pd.read_csv(INPUT)
    features = [c for c in d if c.startswith("log1p_") and d[c].notna().sum() >= 30]
    if len(features) < 3 or "spatial_block" not in d or d.spatial_block.nunique() < 3:
        result = {"status": "not_evaluated", "reason": "At least three measured chemistry features and three coordinate-derived spatial blocks are required.", "metrics": None}
    else:
        X = d[features]
        groups = d.spatial_block.fillna("unknown").astype(str)
        splitter = GroupKFold(n_splits=min(5, groups.nunique()))
        folds = []
        for fold, (tr, te) in enumerate(splitter.split(X, groups=groups), 1):
            pipe = make_pipeline(SimpleImputer(strategy="median"), RobustScaler(), IsolationForest(n_estimators=300, contamination=0.05, random_state=41, n_jobs=-1))
            pipe.fit(X.iloc[tr])
            detector = pipe[-1]
            xte = pipe[:-1].transform(X.iloc[te])
            scores = detector.score_samples(xte)
            flags = detector.predict(xte) == -1
            folds.append({"fold": fold, "n_heldout": len(te), "n_spatial_blocks": groups.iloc[te].nunique(), "mean_score": float(np.mean(scores)), "median_score": float(np.median(scores)), "flagged_fraction_at_assumed_5pct_contamination": float(np.mean(flags))})
        result = {"status": "score_stability_only", "method": "GroupKFold by 0.1-degree rounded coordinate cell; fit IsolationForest on other blocks and score held-out blocks", "metrics": None, "folds": folds, "interpretation": "No labels exist, so this is not predictive validation and no accuracy/AUC/RMSE is reported. The 5% detector contamination is a declared operating assumption, not an observed prevalence or risk probability."}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
