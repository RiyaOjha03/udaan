"""Create time-safe chemistry and geometry features; never impute missing hydrogeology."""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "processed" / "sample_chemistry.csv"
OUTPUT = ROOT / "data" / "processed" / "model_features.csv"
CHEM = ["uranium_mg_l", "arsenic_mg_l", "nitrate_n_mg_l", "fluoride_mg_l", "selenium_mg_l", "ph", "tds_mg_l", "sulfate_mg_l", "chloride_mg_l"]


def main() -> None:
    d = pd.read_csv(INPUT, parse_dates=["sample_date"])
    d = d.sort_values(["site_id", "sample_date", "activity_id"])
    for c in CHEM:
        if c in d:
            # log1p is defined for nonnegative concentrations; pH is left untransformed.
            if c != "ph":
                d[f"log1p_{c}"] = np.log1p(d[c].clip(lower=0))
            # Past-only within-site difference; the first observation remains missing.
            d[f"prior_delta_{c}"] = d.groupby("site_id")[c].diff()
    if {"latitude", "longitude"}.issubset(d.columns):
        # Coarse cell is for grouped validation only, not a source-distance or flow-direction surrogate.
        d["spatial_block"] = d.latitude.round(1).astype("string") + "_" + d.longitude.round(1).astype("string")
    d.to_csv(OUTPUT, index=False)
    print(f"Wrote {len(d):,} observed sample rows to {OUTPUT}")


if __name__ == "__main__":
    main()
