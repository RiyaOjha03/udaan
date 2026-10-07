"""Fit a cautious unsupervised chemistry-anomaly model only if real paired data support it."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import RobustScaler

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "processed" / "model_features.csv"
MODEL_DIR = ROOT / "models"
METRICS = ROOT / "outputs" / "metrics"
FEATURE_PREFIX = "log1p_"


def main() -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    METRICS.mkdir(parents=True, exist_ok=True)
    if not INPUT.exists():
        status = {"status": "not_fit", "reason": "No multivariate cleaned records. Run data_download.py and data_cleaning.py; uranium-only records do not support a multivariate vulnerability model."}
    else:
        d = pd.read_csv(INPUT)
        features = [c for c in d if c.startswith(FEATURE_PREFIX) and d[c].notna().sum() >= 30]
        X = d[features].replace([np.inf, -np.inf], np.nan) if features else pd.DataFrame()
        usable = X.notna().sum(axis=1) >= 3 if features else pd.Series(False, index=d.index)
        X = X.loc[usable]
        if len(features) < 3 or len(X) < 100:
            status = {"status": "not_fit", "reason": "Requires at least 3 measured log-concentration/chemistry features and 100 co-sampled records with at least 3 available features. No synthetic rows are created.", "n_candidate_features": len(features), "n_usable_records": len(X), "features": features}
        else:
            model = make_pipeline(SimpleImputer(strategy="median"), RobustScaler(), IsolationForest(n_estimators=400, contamination=0.05, random_state=41, n_jobs=-1))
            model.fit(X)
            scores = model.score_samples(X)
            labels = model.predict(X)
            scores_df = d.loc[X.index, [c for c in ["site_id", "sample_date", "latitude", "longitude", "spatial_block"] if c in d]].copy()
            scores_df["anomaly_score"] = scores
            scores_df["relative_outlier_flag_assumed_5pct"] = labels == -1
            scores_df.to_csv(METRICS / "unsupervised_anomaly_scores.csv", index=False)
            joblib.dump(model, MODEL_DIR / "isolation_forest.joblib")
            status = {"status": "fit", "model": "sklearn IsolationForest", "target": None, "n_records": len(X), "features": features, "assumed_contamination": 0.05, "random_state": 41, "score_definition": "IsolationForest score_samples; relative multivariate unusualness in this extracted reference dataset; not a degradation probability, risk category, future prediction, or source attribution.", "supervised_performance_metrics": None, "spatial_validation": "See outputs/metrics/spatial_score_stability.json; score stability is not predictive validation.", "limitation": "No validated ISR degradation outcome labels or site-linked operational/baseline time series are available. The model must not be described as an ISR impact/vulnerability predictor."}
    (MODEL_DIR / "model_status.json").write_text(json.dumps(status, indent=2), encoding="utf-8")
    print(json.dumps(status, indent=2))


if __name__ == "__main__":
    main()
