"""Quantify observable-data completeness and emit rule-based research monitoring suggestions."""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "reports"

EXPECTED = {
    "uranium_mg_l": "ISR-related analyte; distinguish native background from excursions with baseline and temporal series.",
    "arsenic_mg_l": "Potentially mobilized/metalloid co-contaminant; a uranium-only panel misses co-occurring chemistry.",
    "selenium_mg_l": "Potentially relevant co-contaminant in uranium-bearing aquifer settings.",
    "nitrate_n_mg_l": "Useful broader groundwater-quality context; not a unique ISR tracer.",
    "fluoride_mg_l": "Groundwater-quality constituent; pairs with other chemistry for general geochemical context.",
    "ph": "Controls aqueous speciation and sorption; field measurement method and date matter.",
    "sulfate_mg_l": "Major-ion context can help characterize water chemistry and restoration trends.",
    "tds_mg_l": "Bulk dissolved-solids measure; does not identify source.",
    "chloride_mg_l": "Major-ion context; not a unique ISR tracer and needs site-specific interpretation.",
}


def main() -> None:
    sample = ROOT / "data" / "processed" / "sample_chemistry.csv"
    baseline = ROOT / "data" / "processed" / "usgs_groundwater_uranium.csv"
    OUT.mkdir(parents=True, exist_ok=True)
    items, score = [], None
    if sample.exists():
        d = pd.read_csv(sample)
        n = len(d)
        chemical = sum(float(d[c].notna().mean()) for c in EXPECTED if c in d) / len(EXPECTED)
        spatial = float(d[["latitude", "longitude"]].notna().all(axis=1).mean()) if {"latitude", "longitude"}.issubset(d) else 0.0
        hydro_fields = ["aquifer_name", "aquifer_type", "well_depth_value"]
        hydro = sum(float(d[c].notna().mean()) for c in hydro_fields if c in d) / len(hydro_fields)
        dates = pd.to_datetime(d.sample_date, errors="coerce")
        years = max((dates.max() - dates.min()).days / 365.25, 0) if dates.notna().any() else 0
        repeats = float((d.groupby("site_id").size() >= 2).mean()) if n else 0
        temporal = min(1.0, years / 5) * repeats
        score = round(100 * (.40 * chemical + .20 * spatial + .20 * hydro + .20 * temporal))
        for c, why in EXPECTED.items():
            frac = float(d[c].notna().mean()) if c in d else 0.0
            if frac < .8:
                items.append({"gap": c, "coverage_fraction": round(frac, 3), "why_it_matters": why, "suggested_action": "Pair this analyte with other measurements at the same site/date and document method, fraction, units, and detection limits."})
        for col, why in [("latitude", "Coordinates support spatial coverage review; they do not establish flow."), ("well_depth_value", "Depth/screen interval is needed to compare hydraulically relevant observations."), ("aquifer_name", "Aquifer identity is needed to interpret connectivity and transferability.")]:
            frac = float(d[col].notna().mean()) if col in d else 0.0
            if frac < .8:
                items.append({"gap": col, "coverage_fraction": round(frac, 3), "why_it_matters": why, "suggested_action": "Recover from well construction/site metadata or field records; do not impute as observed."})
        if repeats < .8 or years < 3:
            items.append({"gap": "baseline and repeated temporal sampling", "coverage_fraction": round(repeats, 3), "why_it_matters": "A single cross-sectional result cannot estimate baseline deviation, trend, restoration, or degradation.", "suggested_action": "Prioritize repeat sampling at comparable wells and methods across pre-operation, operational, and post-restoration periods where such phases actually exist."})
    elif baseline.exists():
        b = pd.read_csv(baseline)
        expected_n = len(EXPECTED)
        chemical = 1 / expected_n
        coord = 0.0
        hydro = 0.0
        stations_path = ROOT / "data" / "raw" / "wqp_uranium_stations.csv"
        if stations_path.exists():
            st = pd.read_csv(stations_path, low_memory=False)
            site_col = "MonitoringLocationIdentifier"
            located = st.dropna(subset=["LatitudeMeasure", "LongitudeMeasure"]) if {"LatitudeMeasure", "LongitudeMeasure"}.issubset(st.columns) else st.iloc[0:0]
            coord = min(1.0, located[site_col].nunique() / max(b.site.nunique(), 1))
            hcols = ["AquiferName", "AquiferTypeName", "WellDepthMeasure/MeasureValue"]
            rates = []
            for c in hcols:
                if c in st:
                    val = st[c].astype(str).str.strip().str.lower()
                    rates.append(float((~val.isin(["", "nan", "none", "unknown", "not determined"])).mean()))
            hydro = sum(rates) / len(hcols)
        counts = b.groupby("site").size()
        repeat = float((counts >= 2).mean()) if len(counts) else 0
        dates = pd.to_datetime(b.date, errors="coerce")
        span = max((dates.max() - dates.min()).days / 365.25, 0) if dates.notna().any() else 0
        temporal = min(1.0, span / 5) * repeat
        score = round(100 * (.4 * chemical + .2 * coord + .2 * hydro + .2 * temporal))
        items = [{"gap": "co-sampled multianalyte chemistry", "coverage_fraction": round(chemical, 3), "why_it_matters": "The baseline extract contains uranium only; multivariate anomaly analysis and co-contaminant interpretation are unsupported.", "suggested_action": "Run the documented multi-parameter WQP downloader and verify shared activity identifiers."}, {"gap": "hydraulic head, gradient, and flow direction", "coverage_fraction": 0.0, "why_it_matters": "Coordinates alone do not identify upgradient/downgradient connectivity.", "suggested_action": "Obtain contemporaneous water-level elevations from a hydrogeologist and derive gradient only within a defensible connected aquifer."}, {"gap": "well screen, aquifer/geology, site baseline and ISR-zone geometry", "coverage_fraction": round(hydro, 3), "why_it_matters": "Optional station attributes are incomplete and do not provide screen intervals, site baseline phases, or connected ISR geometry.", "suggested_action": "Add verified well construction, aquifer framework, repeated baseline data, and user-supplied hypothetical ISR polygon; preserve scenario labels."}, {"gap": "phase-linked temporal baseline", "coverage_fraction": round(temporal, 3), "why_it_matters": "Repeated national observations do not establish matched pre-operation, operation, and restoration sampling at one ISR site.", "suggested_action": "Acquire repeated site-specific measurements with documented phase, method, and detection limits."}]
    n_records = len(pd.read_csv(sample if sample.exists() else baseline)) if sample.exists() or baseline.exists() else 0
    report = {"status": "descriptive_completeness_not_risk", "overall_completeness_score_percent": score, "components": {"chemistry": round(chemical, 3) if 'chemical' in locals() else None, "spatial_coordinates": round(spatial, 3) if sample.exists() and 'spatial' in locals() else round(coord, 3) if 'coord' in locals() else None, "hydrogeology": round(hydro, 3) if 'hydro' in locals() else None, "temporal": round(temporal, 3) if 'temporal' in locals() else None}, "score_definition": "Coverage rubric only: chemistry 40%, spatial coordinates 20%, hydrogeology metadata 20%, temporal span/repeated-site sampling 20%. Missingness is not a vulnerability score; repeated national records are not ISR phase coverage.", "n_records": n_records, "data_gaps": items, "monitoring_recommendations": [{"priority": i + 1, "recommendation": x["suggested_action"], "basis": x["gap"], "label": "AI-assisted monitoring recommendations for research and decision support; not a regulatory requirement."} for i, x in enumerate(items)]}
    (OUT / "data_gap_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
