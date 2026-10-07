"""Reproducible WQP downloads for observed groundwater chemistry and station metadata."""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
BASE = "https://www.waterqualitydata.us/data"
PCODES = ["22703", "01002", "00618", "00950", "01145", "00400", "70300", "00945", "00940"]


def fetch(url: str, target: Path, timeout: int) -> None:
    req = Request(url, headers={"User-Agent": "ISR-Groundwater-Decision-Support/1.0"})
    partial = target.with_suffix(target.suffix + ".part")
    try:
        with urlopen(req, timeout=timeout) as response, partial.open("wb") as dst:
            while chunk := response.read(1024 * 1024):
                dst.write(chunk)
        if partial.stat().st_size < 100:
            raise RuntimeError(f"Unexpectedly small response: {partial}")
        with partial.open("rb") as check:
            header = check.readline(4096).decode("utf-8-sig", errors="replace").lower()
        if "," not in header or "monitoringlocation" not in header:
            raise RuntimeError(f"Response does not look like WQP CSV: {partial}")
        os.replace(partial, target)
    except Exception:
        partial.unlink(missing_ok=True)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", help="Optional USGS state FIPS, e.g. 56 for Wyoming; omitted means national query.")
    parser.add_argument("--start-date", help="Optional earliest sample date MM-DD-YYYY.")
    parser.add_argument("--timeout", type=int, default=300)
    args = parser.parse_args()
    RAW.mkdir(parents=True, exist_ok=True)
    params: list[tuple[str, str]] = [("pCode", ";".join(PCODES)), ("mimeType", "csv"), ("zip", "no"), ("providers", "NWIS"), ("sampleMedia", "Water")]
    if args.state:
        params.append(("statecode", f"US:{args.state}"))
    if args.start_date:
        params.append(("startDateLo", args.start_date))
    results_url = f"{BASE}/Result/search?{urlencode(params)}"
    station_params = [("pCode", ";".join(PCODES)), ("mimeType", "csv"), ("zip", "no"), ("providers", "NWIS")]
    if args.state:
        station_params.append(("statecode", f"US:{args.state}"))
    stations_url = f"{BASE}/Station/search?{urlencode(station_params)}"
    retrieved = datetime.now(timezone.utc).isoformat()
    for url, name in [(results_url, "wqp_groundwater_results.csv"), (stations_url, "wqp_groundwater_stations.csv")]:
        target = RAW / name
        print(f"Downloading {name} ...")
        fetch(url, target, args.timeout)
        if target.stat().st_size < 100:
            raise RuntimeError(f"Unexpectedly small response: {target}")
    manifest = {
        "retrieved_utc": retrieved,
        "provider": "USGS NWIS via Water Quality Portal",
        "results_url": results_url,
        "stations_url": stations_url,
        "parameters": {"pCodes": PCODES, "description": "Uranium, dissolved arsenic, nitrate as N, fluoride, selenium, field pH, total dissolved solids, sulfate, chloride"},
        "filters": {"media": "Water; groundwater subdivision is checked during cleaning", "optional_state_fips": args.state, "optional_start_date": args.start_date},
        "limitations": ["Parameter availability and units differ among sites and dates.", "A multi-analyte query does not guarantee same-activity co-sampling.", "The NWIS provider subset is not all WQP contributors."],
    }
    (RAW / "wqp_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("Download complete; provenance saved to data/raw/wqp_manifest.json")


if __name__ == "__main__":
    main()
