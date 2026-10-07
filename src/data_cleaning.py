"""Normalize WQP results, preserve provenance, and assemble co-sampled records."""
from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW, OUT = ROOT / "data" / "raw", ROOT / "data" / "processed"
CODE_MAP = {
    "22703": ("uranium_mg_l", "ug/l"), "01002": ("arsenic_mg_l", "ug/l"),
    "00618": ("nitrate_n_mg_l", "mg/l"), "00950": ("fluoride_mg_l", "mg/l"),
    "01145": ("selenium_mg_l", "ug/l"),
    "00400": ("ph", "unitless"), "70300": ("tds_mg_l", "mg/l"), "00945": ("sulfate_mg_l", "mg/l"), "00940": ("chloride_mg_l", "mg/l"),
}


def normalize_measure(value: object, unit: object, expected: str) -> float:
    number = pd.to_numeric(value, errors="coerce")
    if pd.isna(number):
        return np.nan
    u = str(unit or "").strip().lower().replace("μ", "µ")
    if expected == "unitless":
        return float(number)
    if u in {"ug/l", "µg/l", "ug/l as n"}:
        return float(number) / 1000.0
    if u in {"mg/l", "mg/l as n"}:
        return float(number)
    return np.nan


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    result_path = RAW / "wqp_groundwater_results.csv"
    station_path = RAW / "wqp_groundwater_stations.csv"
    if not result_path.exists():
        raise FileNotFoundError("Run python src/data_download.py first. The existing uranium-only data are not multivariate.")
    d = pd.read_csv(result_path, low_memory=False)
    required = {"MonitoringLocationIdentifier", "ActivityIdentifier", "ActivityStartDate", "ActivityMediaName", "ActivityMediaSubdivisionName", "USGSPCode", "ResultMeasureValue", "ResultMeasure/MeasureUnitCode"}
    missing = required.difference(d.columns)
    if missing:
        raise ValueError(f"WQP schema missing required fields: {sorted(missing)}")
    d = d[(d.ActivityMediaName == "Water") & (d.ActivityMediaSubdivisionName.astype(str).str.contains("Groundwater", case=False, na=False))].copy()
    d["code"] = d.USGSPCode.astype(str).str.extract(r"(\d{5})", expand=False)
    d = d[d.code.isin(CODE_MAP)].copy()
    d["feature"], d["expected_unit"] = zip(*d.code.map(CODE_MAP))
    d["value"] = [normalize_measure(v, u, e) for v, u, e in zip(d["ResultMeasureValue"], d["ResultMeasure/MeasureUnitCode"], d.expected_unit)]
    d.loc[d.value < 0, "value"] = np.nan
    d["sample_date"] = pd.to_datetime(d.ActivityStartDate, errors="coerce", utc=True).dt.strftime("%Y-%m-%d")
    d["site_id"] = d.MonitoringLocationIdentifier
    d["activity_id"] = d.ActivityIdentifier
    d = d.dropna(subset=["value", "site_id", "sample_date"])
    if d.empty:
        raise ValueError("No numeric groundwater results for configured analyte codes. Keep raw export and review pCodes/media/units before modeling.")
    # Keep measurement method/fraction in audit extract; repeated analytes in the same activity use median.
    d.to_csv(OUT / "normalized_results_audit.csv", index=False)
    sample = d.groupby(["site_id", "sample_date", "activity_id", "feature"], as_index=False).value.median()
    sample = sample.pivot(index=["site_id", "sample_date", "activity_id"], columns="feature", values="value").reset_index()
    sample.columns.name = None
    if station_path.exists():
        s = pd.read_csv(station_path, low_memory=False)
        cols = {"MonitoringLocationIdentifier": "site_id", "LatitudeMeasure": "latitude", "LongitudeMeasure": "longitude", "MonitoringLocationName": "site_name", "MonitoringLocationTypeName": "site_type", "AquiferName": "aquifer_name", "LocalAqfrName": "local_aquifer_name", "AquiferTypeName": "aquifer_type", "WellDepthMeasure/MeasureValue": "well_depth_value", "WellDepthMeasure/MeasureUnitCode": "well_depth_unit"}
        s = s.rename(columns=cols)
        keep = [c for c in cols.values() if c in s.columns]
        s = s[keep].drop_duplicates("site_id")
        sample = sample.merge(s, on="site_id", how="left")
    sample.to_csv(OUT / "sample_chemistry.csv", index=False)
    # Summary is descriptive of extracted data, not a model result.
    feature_cols = sorted({v[0] for v in CODE_MAP.values()})
    report = {
        "n_measurement_rows": int(len(d)), "n_sample_records": int(len(sample)), "n_sites": int(sample.site_id.nunique()),
        "dates_min": str(sample.sample_date.min()) if len(sample) else None, "dates_max": str(sample.sample_date.max()) if len(sample) else None,
        "feature_coverage": {f: {"n": int(sample[f].notna().sum()) if f in sample else 0, "fraction": float(sample[f].notna().mean()) if f in sample else 0.0} for f in feature_cols},
        "coordinate_coverage": float(sample[["latitude", "longitude"]].notna().all(axis=1).mean()) if {"latitude", "longitude"}.issubset(sample.columns) and len(sample) else 0.0,
        "hydrogeology": {c: int(sample[c].notna().sum()) if c in sample else 0 for c in ["aquifer_name", "aquifer_type", "well_depth_value"]},
        "provenance": str((RAW / "wqp_manifest.json").relative_to(ROOT)) if (RAW / "wqp_manifest.json").exists() else "WQP; see data/raw",
    }
    (OUT / "data_profile.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
