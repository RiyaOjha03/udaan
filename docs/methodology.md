# Research Methodology

## 1. Abstract and problem statement

The research question is whether real groundwater chemistry, spatial records, and hydrogeological context can support interpretable assessment of quality change and aquifer vulnerability down-gradient from a hypothetical uranium in-situ recovery (ISR) operation. Existing project functionality is a drinking-water screening interface plus an empirical cumulative uranium reference distribution built from USGS NWIS observations served by the Water Quality Portal (WQP). The project extends this baseline with reproducible ingestion, data-quality auditing, spatial summaries, data-gap analysis, monitoring support, and a conditional unsupervised chemistry-anomaly detector. It does not currently establish an ISR degradation target or predict a real site's impact.

## 2. Motivation, research gap, objectives

Groundwater quality reflects interacting geology, redox and aqueous chemistry, well construction, and groundwater movement. Uranium ISR (also called in-situ leach/recovery) circulates a leaching solution through a uranium-bearing aquifer and recovers uranium through wells; restoration and monitoring are distinct lifecycle phases. EPA's ISR work discusses restoration, excursions, migration, monitoring, and data gaps. Public national observations are heterogeneous and not automatically tied to one operation or a defined baseline. A defensible system must therefore expose missing causal and hydrogeological context, avoid random-split leakage, preserve measurement provenance, and separate empirical reference from impact prediction.

Objectives: (1) preserve primary and secondary chemistry screening; (2) establish real-data provenance and cleaning; (3) inspect hydrogeological/spatiotemporal coverage; (4) implement a model that only runs when multivariate records support it; (5) provide grouped spatial score diagnostics; (6) map observed measurements without representing them as a forecast; (7) quantify coverage gaps and propose research monitoring actions.

## 3. Dataset and provenance

The executed baseline is the WQP Result service, NWIS provider, uranium characteristic. It is filtered to Water/Groundwater and numeric nonnegative results in µg/L. The downloaded station service supplies location type, coordinates, and optional well/aquifer fields. Raw exports and an observation-level filtered CSV are retained. WQP combines heterogeneous methods, dates, reporting limits, and programs; repeated observations at a site are not independent samples. Coordinate completeness is not evidence of flow connectivity. The reproducible multivariate query requests uranium, arsenic, nitrate, fluoride, selenium, pH, TDS, sulfate, and chloride. It has not completed in this environment; the code records the full query and refuses to call the single-analyte baseline multivariate training data.

## 4. Existing screening

Existing screening compares user-entered constituents against EPA primary MCLs and secondary guidelines and reports a uranium empirical percentile. The percentile answers only where a value ranks in the observed reference sample. It is not a safety threshold, a health risk, an ISR-source attribution, or an outcome prediction.

## 5. Data quality and feature engineering

Cleaning filters groundwater media, maps documented USGS parameter codes, parses numeric measures, converts compatible µg/L concentrations to mg/L, and preserves audit rows. The pivot key is site + sample date + activity identifier; replicate results are summarized by median within that activity/feature. This pairing rule is conservative but does not remove cross-laboratory/method heterogeneity. Incompatible units and nonnumeric/censored textual results remain missing rather than being silently coerced.

Candidate features are measured chemistry and log1p concentration for nonnegative concentrations. The within-site first difference is sorted by sampling time and uses only the prior observed value; first differences remain missing. It is not a baseline-adjusted operational effect. Rounded coordinate cells are used only as spatial grouping units for validation. No distance-to-source, upgradient/downgradient, gradient, or geology proxy is invented. IDs, coordinates, and date are excluded as chemistry detector inputs.

## 6. Target definition and ML methodology

The scientifically preferred future supervised target is a within-well change from a pre-operation baseline for specified analytes, linked to actual ISR phase, aquifer, and hydraulic connectivity. This would need prespecified temporal windows, comparable methods, adequate sample sizes, and independent site review. The current records do not contain the requisite site-linked operation or baseline labels. Creating labels from MCL exceedance or uranium concentration would answer a different question and risk circularity/leakage; therefore no supervised classifier or regression is fit.

The gated experimental model is scikit-learn Isolation Forest. It requires at least three measured log-concentration features and at least 100 co-sampled rows with three available features. Median imputation and robust scaling are fit inside the pipeline. Detector contamination (default 0.05) controls a flagging threshold and is not empirical prevalence. Scores mean relative multivariate unusualness within this extracted sample only. They are not vulnerability probabilities, prediction of future degradation, or evidence of ISR causality. The current baseline extract is univariate; the model script should report `not_fit` for it.

## 7. Spatial and temporal validation

For an unsupervised score, conventional predictive metrics and supervised train/test splits are not meaningful without outcomes. The optional grouped check leaves coordinate-derived rounded blocks out while fitting other blocks and reports score distribution/flag fraction for held-out blocks. It is a score-stability diagnostic, not accuracy or validation of a risk model. Nearby wells may share geochemical and hydrogeological structure, so random row splits can leak local patterns. A site-specific future prediction needs spatial-block or leave-location-out validation at the intended prediction distance, plus temporal forward holdout if phases/times support it. No such ISR-specific validation has run.

## 8. Explainability

The baseline percentile is exactly rank-based and does not need SHAP. The unsupervised implementation computes feature-ablation sensitivity and, with optional dependencies installed, Kernel SHAP on the detector's raw score. These explain relative anomaly score only, not degradation probability, health risk, causal effect, or ISR impact. Correlated predictors can make attribution hard to interpret. SHAP for a validated supervised task remains planned until a defensible target and spatial/temporal validation exist.

## 9. Mapping and scenario boundaries

GeoJSON/CSV/map outputs summarize measured uranium by located monitoring site. Marker context may include the drinking-water MCL, but is labelled observed and descriptive. It contains no predicted aquifer vulnerability or risk zones. There is no hypothetical ISR source point/polygon because the scenario location was not supplied. Any later scenario layer must have an explicit hypothetical label and stay separate from observations and model output.

## 10. Data-gap analysis and monitoring recommendations

The implemented completeness rubric weights chemical coverage (40%), location-coordinate coverage (20%), hydrogeology metadata (20%), and repeated-site temporal coverage/span (20%). It is a transparent data-availability score, not a risk or confidence probability. Gaps include co-sampled chemistry, heads/screens/gradient, aquifer identity/connectivity, source geometry, repeated baseline and operation-phase samples, and method/detection metadata. Recommendations ask for paired repeated sampling and verified hydrogeological context, and are research decision support rather than regulatory direction. New well placement should follow a site-specific flow model and existing permit/monitoring requirements.

## 11. Literature review summary

Groundwater ML reviews emphasize data quality, feature/model selection, and interpretability. Groundwater vulnerability comparisons show that method choice and data completeness can materially affect vulnerability mapping; a map is not automatically a validated forecast. Spatial validation literature documents optimistic error under spatial dependence and recommends structured resampling when the goal is spatial transfer. Uranium occurrence reviews show that geochemical speciation, redox, lithology, and water-rock interactions influence mobility. EPA ISR documents emphasize baseline chemistry, excursion monitoring, restoration, stability, offsite migration questions, and remaining data gaps. Groundwater monitoring-network literature treats placement and frequency as hydrogeology- and objective-dependent. SHAP is a principled feature-attribution framework for a fitted prediction function; it is not appropriate to relabel empirical ranks or simple score-ablation as SHAP. These sources motivate transparent uncertainty and data-gap reporting rather than generic risk mapping.

The review specifically covers: groundwater quality prediction (Haggerty et al.); spatial groundwater quality mapping and the distinction between hazard/vulnerability/risk terminology (*Water* 2025 systematic review); aquifer vulnerability comparisons (Yang et al.); uranium hydrogeochemistry (Gao et al.); uranium ISR restoration, potential vulnerabilities, monitoring and data gaps (EPA 2017 and EPA draft monitoring report); spatial cross-validation (Roberts et al.; Meyer & Pebesma); explainable AI foundations (Lundberg & Lee); and groundwater monitoring-network design (Loaiciga et al.). See the linked full citations in the README.

## 12. Results and status

The real uranium reference dataset and screening baseline are available. The multivariate WQP query timed out during retrieval in this run; no partial response is used as an analysis dataset. Therefore: data cleaning/feature generation on a multivariate extract, Isolation Forest results, spatial score stability, explainability outputs, and ISR predictive performance are **not yet evaluated**. No synthetic data or invented metrics are present.

## 13. Limitations and future work

National observations are not site-specific ISR monitoring; sample methods, detection limits, aquifers, time periods, and sampling designs vary. The baseline does not establish source, transport, trend, or aquifer vulnerability. Obtain permit/site geometry, well construction and screens, aquifer framework, contemporaneous water levels, background chemistry, redox/major-ion context, repeated phase-labelled measurements, and hydrogeologist-reviewed flow paths. Then prespecify outcomes, compare suitable baselines, evaluate spatial/temporal holdouts, quantify applicability, and use explanations only within validated scope.
