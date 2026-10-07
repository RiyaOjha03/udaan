"""Model-agnostic score ablation; explicitly not SHAP or causal attribution."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import joblib
try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None
try:
    import shap
except ImportError:
    shap = None

ROOT = Path(__file__).resolve().parents[1]
XFILE = ROOT / "data" / "processed" / "model_features.csv"
MODEL = ROOT / "models" / "isolation_forest.joblib"
OUT = ROOT / "outputs" / "metrics" / "feature_ablation.csv"
FIGURES = ROOT / "outputs" / "figures"


def main() -> None:
    status_path = ROOT / "models" / "model_status.json"
    status = json.loads(status_path.read_text()) if status_path.exists() else {"status": "not_fit"}
    if status.get("status") != "fit":
        print("Explainability not run: no fitted unsupervised model.")
        return
    d = pd.read_csv(XFILE)
    features = status["features"]
    X = d[features]
    model = joblib.load(MODEL)
    base = model.score_samples(X)
    medians = X.median(numeric_only=True)
    rows = []
    for feature in features:
        altered = X.copy()
        altered[feature] = medians[feature]
        delta = model.score_samples(altered) - base
        rows.append({"feature": feature, "mean_absolute_score_change_when_set_to_training_median": float(np.mean(np.abs(delta))), "note": "Ablation sensitivity, not SHAP value, causation, or feature importance in a supervised target."})
    pd.DataFrame(rows).sort_values("mean_absolute_score_change_when_set_to_training_median", ascending=False).to_csv(OUT, index=False)
    print(f"Saved descriptive score ablation to {OUT}")
    if shap is None or plt is None:
        print("Optional SHAP/matplotlib packages are not installed; score-ablation output is available. Install requirements-xai.txt to enable SHAP.")
        return
    # Kernel SHAP attributes the detector's raw anomaly score only. It does not explain
    # degradation probability, health risk, or causal effect. Limit samples for reproducibility.
    FIGURES.mkdir(parents=True, exist_ok=True)
    background = X.sample(min(40, len(X)), random_state=41)
    explain = X.sample(min(50, len(X)), random_state=42)
    explainer = shap.KernelExplainer(model.score_samples, background)
    values = explainer.shap_values(explain, nsamples=120)
    values = np.asarray(values)
    if values.ndim == 3:
        values = values[0]
    shap_df = pd.DataFrame(values, columns=features)
    shap_df.insert(0, "site_id", d.loc[explain.index, "site_id"].values if "site_id" in d else "")
    shap_df.to_csv(ROOT / "outputs" / "metrics" / "anomaly_score_shap_values.csv", index=False)
    plt.figure()
    shap.summary_plot(values, explain, show=False, plot_type="bar")
    plt.tight_layout()
    plt.savefig(FIGURES / "anomaly_score_shap_summary.png", dpi=160, bbox_inches="tight")
    plt.close("all")
    print("Saved SHAP attribution for raw unsupervised anomaly score; this is not a risk explanation.")


if __name__ == "__main__":
    main()
