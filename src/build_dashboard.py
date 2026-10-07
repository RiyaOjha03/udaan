"""Embed current verified project status in the offline dashboard shell."""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "index.html"


def read_json(path: Path, default: dict) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def main() -> None:
    ref = read_json(ROOT / "uranium_model.json", {})
    gaps = read_json(ROOT / "outputs" / "reports" / "data_gap_report.json", {})
    model = read_json(ROOT / "models" / "model_status.json", {"status": "not_evaluated", "reason": "No processed multivariate data available."})
    profile = read_json(ROOT / "data" / "processed" / "data_profile.json", {})
    obs = ROOT / "data" / "processed" / "usgs_groundwater_uranium.csv"
    baseline_n = len(pd.read_csv(obs)) if obs.exists() else ref.get("n", 0)
    snapshot = {"as_of": ref.get("retrieved_utc", ""), "reference": {"n": ref.get("n", baseline_n), "sites": ref.get("unique_sites", 0), "median_ug_l": ref.get("median"), "p90_ug_l": ref.get("p90"), "mcl_ug_l": 30}, "observed_rows": baseline_n, "data_profile": profile, "model": model, "gaps": gaps, "map_available": (ROOT / "outputs" / "maps" / "observed_map.html").exists(), "status_label": "Baseline screening operational; ISR degradation prediction not evaluated"}
    marker_a, marker_b = "/* SNAPSHOT_START */", "/* SNAPSHOT_END */"
    text = HTML.read_text(encoding="utf-8")
    before, rest = text.split(marker_a, 1)
    _, after = rest.split(marker_b, 1)
    HTML.write_text(before + marker_a + "\nconst SNAPSHOT = " + json.dumps(snapshot, separators=(",", ":")) + ";\n" + marker_b + after, encoding="utf-8")
    print("Dashboard snapshot refreshed from current local data and pipeline status.")


if __name__ == "__main__":
    main()
