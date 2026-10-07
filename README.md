# AI-Enabled Groundwater Quality & Aquifer Vulnerability Decision Support

Software-only research prototype for water-quality screening and monitoring design around a **hypothetical uranium in-situ recovery (ISR) operation**. It makes no claim about a real ISR site's impact. The project is structured for an undergraduate Mining CPS research demonstration, including the TEXMiN–BIT Sindri Mining CPS CoE UG Fellowship Program 2026 context; it is not an endorsed program deliverable.

## Abstract

The project extends an existing browser-based chemistry screener and empirical uranium reference distribution into a reproducible research workspace. The current verified baseline uses public USGS NWIS uranium observations distributed through the Water Quality Portal (WQP); the app compares entered chemistry with selected U.S. drinking-water references and positions uranium in the empirical observed distribution. Supporting pipeline modules download and audit WQP chemistry and site metadata, normalize result units, assemble co-sampled records, create time-safe features, gate an unsupervised Isolation Forest, perform spatial-block score-stability analysis, export observed data to GIS, and report data gaps and monitoring suggestions. The current extract is uranium-only for the executed baseline. It does not include site-linked ISR operations, validated degradation labels, water-level/flow context, or verified ISR geometry. Consequently, ISR degradation prediction is **not yet evaluated**; no performance metrics or risk predictions are claimed.

## Start the dashboard

Open `index.html` in a modern browser. The original screening module is preserved in `screening.html` and embedded in the dashboard. The app runs locally. The observed map uses OpenStreetMap tiles and requires an internet connection; its data points are actual site records.

## Upload to GitHub and deploy

The repository includes `.github/workflows/pages.yml`. After the extracted project is pushed to a GitHub repository's `main` branch, the workflow publishes the browser dashboard with GitHub Pages. In the repository, set **Settings → Pages → Build and deployment → Source → GitHub Actions** if prompted. GitHub Pages serves the static dashboard and map; it does not execute the Python ingestion/model pipeline. Run Python locally, review generated outputs, and push updates to publish them. The map's basemap tiles require internet access.

To upload the ZIP: extract it, create a new GitHub repository, and upload the extracted project files and folders (including the hidden `.github` folder), or use Git with the commands shown below:

`git init -b main` → `git add .` → `git commit -m "Add groundwater ISR decision support project"` → `git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git` → `git push -u origin main`

Uploading the ZIP file itself to GitHub does not unpack it into a deployable repository; extract it first. The ZIP excludes virtual environments, Python bytecode, incomplete download chunks, and local binary model pickle files. Source CSVs and generated GIS outputs are included.

## Reproducible pipeline

Use Python 3.10+ in a virtual environment.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# Optional, only if a fitted detector exists and SHAP analysis is desired:
pip install -r requirements-xai.txt
python train_model.py
python src/data_download.py --state 56
python src/data_cleaning.py
python src/feature_engineering.py
python src/train_models.py
python src/spatial_validation.py
python src/explainability.py
python src/data_gap_analysis.py
python src/vulnerability_mapping.py
python src/build_dashboard.py
```

The state argument is optional; it accepts a two-digit FIPS code to limit query scope. The downloader records the exact requested URLs, filters, parameter codes, and retrieval time. WQP requests can be large or time out; if that happens, narrow the query by state or date and rerun. The project does not treat partial downloads as complete datasets. The provided code currently gates model fitting unless at least 3 measured chemistry features and 100 usable co-sampled records are available.

## Existing baseline vs research contribution

**Existing baseline (operational):** screening for uranium, arsenic, nitrate as N, fluoride, selenium, pH, TDS, sulfate, and chloride; separate primary MCL and secondary guideline results; and an empirical cumulative uranium distribution. Its percentile is descriptive, not a regulatory safety threshold.

**New research software (implemented, execution/data dependent):** reproducible WQP ingestion, result normalization/pivoting, station metadata joining, past-only feature creation, unsupervised anomaly detector, spatial block score stability, score-ablation sensitivity, optional Kernel SHAP attribution of raw anomaly score, observed-data GIS export, completeness rubric, and monitoring recommendations. The real multivariate download and its model execution remain pending because the full co-sample query timed out in the current run. `models/model_status.json` and `outputs/metrics/` report actual status after running; missing outputs are not filled with simulated results.

**Planned/experimental:** a supervised ISR degradation model after obtaining site-linked baseline and operational/restoration observations, hydraulic context, and defensible labels; temporal holdout; verified flow-informed upgradient/downgradient analysis; SHAP attribution for a validated supervised outcome (if supported); and any hypothetical source polygon supplied by the user. No hypothetical ISR polygon is bundled.

## Data and provenance

- Baseline uranium results: [WQP NWIS result service](https://www.waterqualitydata.us/data/Result/search?characteristicName=Uranium&mimeType=csv&zip=no&providers=NWIS), queried for uranium and filtered to `Water / Groundwater`, numeric nonnegative values reported in µg/L. Raw and filtered records are preserved in `data/raw/` and `data/processed/`.
- Station metadata: [WQP NWIS station service](https://www.waterqualitydata.us/data/Station/search?characteristicName=Uranium&mimeType=csv&zip=no&providers=NWIS), including site type, coordinates, and optional aquifer/well attributes. Missing attributes remain missing.
- Multivariate research query: see `src/data_download.py` and the generated `data/raw/wqp_manifest.json`. Parameter codes are recorded there. A multi-parameter query does not guarantee same-activity co-sampling; `data_cleaning.py` joins only measurements sharing activity, site, and sample date.
- The baseline extract contains 9,631 numeric groundwater uranium measurements and 7,684 sites at the current recorded retrieval. These are source records, not independent samples in a designed experiment.

No synthetic measurements are bundled or presented as observed. Hypothetical ISR context is not geolocated on the observed-data map.

## Research target and model status

The scientifically preferred future supervised target is within-well baseline-adjusted change in pre-specified constituents, linked to documented operational/restoration phase and a hydraulically connected aquifer. Such labels and site context are not in the current public baseline. The software therefore does not manufacture labels or train a supervised model.

The conditional Isolation Forest is an **unsupervised reference-data anomaly detector**. It identifies multivariate chemical records that look unusual relative to the extracted dataset. It does not predict degradation, vulnerability, health risk, future concentrations, or ISR causation. The 5% contamination setting is a modeling operating assumption, not a measured prevalence. With no labels, accuracy/AUC/RMSE/R² are inapplicable. Spatial fold outputs are score-stability summaries only, not predictive validation.

## Hydrogeology, map, gaps, recommendations

Coordinates and optional aquifer/well attributes are descriptive. Coordinates alone are not a groundwater gradient. Water-level elevation, screen intervals, hydraulic gradient/direction, aquifer connectivity, verified source footprint, phase labels, and repeated comparable samples are missing or not joined. No downstream/upgradient label is inferred from straight-line distance.

The map exports observed site summaries to GeoJSON and CSV. It distinguishes observed data and never presents them as model prediction or hypothetical ISR data. The data completeness score is a documented coverage rubric (chemistry 40%, spatial coordinates 20%, hydrogeology 20%, temporal/repeated coverage 20%); it is not a risk score. Monitoring recommendations identify missing evidence and are research decision support, not regulatory requirements.

## Project layout

```text
index.html                 Browser decision-support dashboard
screening.html             Preserved original screening/reference module
train_model.py             Existing empirical uranium reference builder
src/data_download.py       WQP result and station ingestion
src/data_cleaning.py       Quality checks, unit normalization, sample pivot
src/feature_engineering.py Time-safe chemistry features and spatial groups
src/train_models.py        Guarded unsupervised anomaly model
src/spatial_validation.py  Coordinate-block score stability (no labels)
src/explainability.py      Score ablation + optional Kernel SHAP for raw anomaly score
src/vulnerability_mapping.py GIS export/map of observed uranium sites
src/data_gap_analysis.py   Coverage score and research monitoring suggestions
src/build_dashboard.py     Embed current generated status into dashboard
data/                      Provenance, raw and processed observations
models/                    Model artifact and model status
outputs/                   Metrics, maps, figures and reports
docs/methodology.md         Research-style methods and limitations
```

## Literature review and references

1. Haggerty, R., Sun, J., Yu, H., & Li, Y. (2023). Application of machine learning in groundwater quality modeling: A comprehensive review. *Water Research*, 233, 119745. [doi:10.1016/j.watres.2023.119745](https://doi.org/10.1016/j.watres.2023.119745).
2. Roberts, D. R. et al. (2017). Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure. *Ecography*, 40, 913–929. [doi:10.1111/ecog.02881](https://doi.org/10.1111/ecog.02881).
3. Meyer, H. & Pebesma, E. (2021). Predicting into unknown space? Estimating the area of applicability of spatial prediction models. *Methods in Ecology and Evolution*, 12, 1620–1633. [doi:10.1111/2041-210X.13650](https://doi.org/10.1111/2041-210X.13650).
4. EPA. (2017). *Aquifer Restoration after Uranium Recovery: Evaluation of Aquifer Restoration at Sample Uranium In-Situ Recovery Sites*. EPA/600/F-17/342. [Technical brief](https://www.epa.gov/research/aquifer-restoration-after-uranium-recovery-evaluation-aquifer-restoration-sample).
5. EPA. (2014). *Ground Water Modeling Studies at In Situ Leaching Facilities and Evaluation of Doses and Risks to Offsite Receptors from Contaminated Ground Water*. EPA-402-F-13-051. [Appendix D](https://www.epa.gov/sites/default/files/2015-05/documents/EPA-402-F-13-051b.pdf).
6. Gao, Y. et al. (2022). A critical review on the occurrence and distribution of uranium- and thorium-decay nuclides and their effect on groundwater quality. *Science of the Total Environment*, 808, 151914. [doi:10.1016/j.scitotenv.2021.151914](https://doi.org/10.1016/j.scitotenv.2021.151914).
7. Loaiciga, H. A. et al. (1992). Review of groundwater quality monitoring network design. *Journal of Hydraulic Engineering*, 118(1), 11–37. [doi:10.1061/(ASCE)0733-9429(1992)118:1(11)](https://doi.org/10.1061/(ASCE)0733-9429(1992)118:1(11)).
8. Lundberg, S. M. & Lee, S.-I. (2017). A unified approach to interpreting model predictions. *NeurIPS 30*. [Proceedings](https://proceedings.neurips.cc/paper/7062-a-unified-approach-tointerpreting-model-predictions).
9. Yang, J. et al. (2025). Advancing groundwater vulnerability assessment to nitrate contamination: index-based, statistical, and ML approaches. *Journal of Hydrology*, 663, 134189. [doi:10.1016/j.jhydrol.2025.134189](https://doi.org/10.1016/j.jhydrol.2025.134189).
10. *Machine Learning Models of the Geospatial Distribution of Groundwater Quality: A Systematic Review* (2025). *Water*, 17(19), 2861. [doi:10.3390/w17192861](https://doi.org/10.3390/w17192861).
11. EPA. Draft technical report on post-closure monitoring at uranium ISR sites, including baseline chemistry, excursion monitoring, and restoration stability. [Report](https://nepis.epa.gov/Exe/ZyPURL.cgi?Dockey=P100VM7M.TXT).
12. EPA. National Primary Drinking Water Regulations and Secondary Drinking Water Standards. [Primary MCLs](https://www.epa.gov/ground-water-and-drinking-water/national-primary-drinking-water-regulations); [secondary guidelines](https://www.epa.gov/sdwa/secondary-drinking-water-standards-guidance-nuisance-chemicals).

## Results

Baseline reference distribution is available from the bundled source extract. Multivariate ML, spatial score stability, and ISR-specific predictive experiments are **not yet evaluated**. No performance metric is claimed. Run the documented pipeline and inspect generated status/metrics before reporting an experiment.
