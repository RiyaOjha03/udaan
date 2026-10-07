"""Build the empirical uranium reference model from real WQP observations.

Uses only Python's standard library. Run from this directory with network access:
    python train_model.py
"""
from __future__ import annotations

import csv
import json
import math
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
SOURCE_URL = (
    "https://www.waterqualitydata.us/data/Result/search?"
    "characteristicName=Uranium&mimeType=csv&zip=no&providers=NWIS"
)
RAW = DATA / "wqp_uranium_all.csv"
GROUNDWATER = DATA / "usgs_groundwater_uranium.csv"
MODEL = ROOT / "uranium_model.json"
APP = ROOT / "screening.html"


def number(value: str) -> float | None:
    try:
        n = float(value.strip())
        return n if math.isfinite(n) else None
    except (ValueError, AttributeError):
        return None


def main() -> None:
    if not RAW.exists() or RAW.stat().st_size < 1000:
        request = urllib.request.Request(SOURCE_URL, headers={"User-Agent": "WaterQualityScreen/1.0"})
        with urllib.request.urlopen(request, timeout=180) as response, RAW.open("wb") as out:
            out.write(response.read())

    rows: list[dict[str, str]] = []
    values: list[float] = []
    with RAW.open(encoding="utf-8-sig", newline="", errors="replace") as source:
        reader = csv.DictReader(source)
        for row in reader:
            if row.get("ActivityMediaName") != "Water" or row.get("ActivityMediaSubdivisionName") != "Groundwater":
                continue
            unit = (row.get("ResultMeasure/MeasureUnitCode") or "").strip().lower()
            if unit not in {"ug/l", "µg/l"}:
                continue
            value = number(row.get("ResultMeasureValue", ""))
            if value is None or value < 0:
                continue
            clean = {
                "date": row.get("ActivityStartDate", ""),
                "site": row.get("MonitoringLocationIdentifier", ""),
                "uranium_ug_l": value,
                "qualifier": row.get("ResultDetectionConditionText", ""),
            }
            rows.append(clean)
            values.append(value)
    if len(values) < 100:
        raise RuntimeError(f"Only {len(values)} usable groundwater results found; source download may be incomplete.")
    with GROUNDWATER.open("w", encoding="utf-8", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=["date", "site", "uranium_ug_l", "qualifier"])
        writer.writeheader()
        writer.writerows(rows)
    values.sort()
    model = {
        "source": "USGS National Water Information System records distributed through the Water Quality Portal (NWIS provider)",
        "source_url": SOURCE_URL,
        "retrieved_utc": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "data_filter": "Water / Groundwater; reported uranium in µg/L; nonnegative numeric results; all detection qualifiers retained as reported.",
        "n": len(values),
        "unique_sites": len({r["site"] for r in rows if r["site"]}),
        "min": values[0],
        "median": values[len(values) // 2],
        "p90": values[math.ceil(.90 * len(values)) - 1],
        "max": values[-1],
        "values_sorted": values,
    }
    MODEL.write_text(json.dumps(model, separators=(",", ":")), encoding="utf-8")
    html = APP.read_text(encoding="utf-8")
    start = "/* MODEL_DATA_START */"
    end = "/* MODEL_DATA_END */"
    before, rest = html.split(start, 1)
    _, after = rest.split(end, 1)
    APP.write_text(before + start + "\nconst MODEL = " + json.dumps(model, separators=(",", ":")) + ";\n" + end + after, encoding="utf-8")
    print(f"Built model from {len(values):,} measured groundwater records at {model['unique_sites']:,} sites.")
    print(f"Saved {GROUNDWATER.name}, {MODEL.name}, and refreshed {APP.name}.")


if __name__ == "__main__":
    main()
