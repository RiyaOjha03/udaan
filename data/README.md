# Data provenance and status

## Existing baseline observations

`raw/wqp_uranium_all.csv` is the full raw Water Quality Portal (WQP) result export for uranium from the USGS NWIS provider. Source query: <https://www.waterqualitydata.us/data/Result/search?characteristicName=Uranium&mimeType=csv&zip=no&providers=NWIS>. `raw/wqp_uranium_stations.csv` is the corresponding station metadata export, including reported location, site type, aquifer and well-depth fields where available. Source query: <https://www.waterqualitydata.us/data/Station/search?characteristicName=Uranium&mimeType=csv&zip=no&providers=NWIS>. Retrieved 2026-10-07.

`raw/baseline_manifest.json` records the source endpoints, retrieval date, baseline query/filters, counts, and limitations. `processed/usgs_groundwater_uranium.csv` is filtered from the raw results by the existing baseline pipeline: groundwater, uranium, numerical nonnegative µg/L result. It preserves date, site, concentration, and qualifier. Rebuild with `python train_model.py`.

## Research pipeline data

The intended multivariate source is the same authoritative WQP/USGS NWIS discrete sample service. The project downloader requests a documented set of co-sample chemistry parameters and station records, then records the exact query and retrieval time in a manifest. The multivariate extract has not yet been successfully retrieved in this environment; do not treat the uranium-only extract as sufficient for the multivariate anomaly model. Groundwater elevation, screened interval, gradient/flow direction, site hydrostratigraphy, baseline-to-operational phase, and a real ISR facility location are also not established in this extract.

No synthetic measurements are bundled or presented as observations. The hypothetical ISR site is not placed on the real station map.
