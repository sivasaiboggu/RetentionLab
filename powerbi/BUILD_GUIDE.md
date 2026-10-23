# RetentionLab: Power BI Desktop build kit

This is an import/build kit, **not a completed .pbix report**. CSVs are direct
exports or transparent groupings of the frozen dashboard artifacts. No model
was retrained and no new measurement is introduced. The layout below is a
specification; it has not been rendered in Power BI Desktop in this environment.

## 1. Import and verify types

1. Open Power BI Desktop on Windows and create a blank report.
2. Home > Get data > Text/CSV. Choose each CSV in this folder, one at a time.
   Use UTF-8 (65001), comma delimiter and first row as headers. Choose Transform
   Data to inspect types, then Close & Apply. Do not import the theme or guide.
3. IDs/counts/segment/topic are Whole Number (topic can be blank). Probability,
   accuracy/AP/F1/risk and scenario fractions are Decimal Number, not whole
   numbers. Text columns stay Text; selected/review flags are True/False.
   If a locale treats dots as separators, Change Type > Using Locale > English
   (United States). Do not round the stored probabilities.
4. In Model view, remove auto-detected relationships. All imported summary
   tables stay disconnected. Turn off Auto date/time for this report if offered;
   these files contain no time series.
5. Check the `exports_manifest.json` file for each source and row count. It is
   a local integrity/provenance map, not proof of independent validation.

## 2. Apply the theme and page layout

1. On current Desktop versions use Design > Browse for themes (older versions:
   View > Themes > Browse for themes). Import `graphite-sage-theme.json`.
2. Select the blank page. Format page > Canvas settings > Custom size:
   width 1220, height 960. Set page background #151D21, transparency 0%.
3. Add a text header at (32,24): `RetentionLab` in Segoe UI Semibold 26pt,
   color #F3F0E7. Add a small subtitle that says `Frozen research evidence`.
4. Visual backgrounds #202B30, 0% transparency; border #35413F; rounded corners
   10px. Set chart series manually to #A8C4A2, text #F3F0E7, grid/rules a muted
   tonal neutral. No rainbow, gradients, stock imagery or paid visuals.
5. Use Segoe UI for cross-machine reliability. Titles 14pt, labels 10pt,
   card values 26pt. Turn category labels on. Remove visual header icons when
   not in use. No shadow or animation is required.
6. For each visual below: click its visual type, drag the fields, then Format >
   General > Properties to set X/Y/width/height. Use the field dropdown to set
   Max (not Sum) on precomputed metrics and percentages. Format percentages in
   Modeling without multiplying their raw fraction by 100.

## Fields and visuals

Do not create relationships: these are disconnected summary tables. Adding a
relationship from KPI/model summaries to customer rows can change fixed metrics
under filters and misrepresent the frozen evaluation.

| Position (x,y,width,height) | Visual | Fields and exact settings |
|---|---|---|
| 32,100,280,90 | Card | kpi_summary.source_customers; aggregation Max; whole number; title Source customers |
| 324,100,280,90 | Card | kpi_summary.holdout_average_precision; Max; 3 decimals; title Holdout AP |
| 616,100,280,90 | Card | kpi_summary.holdout_roc_auc; Max; 3 decimals; title Holdout ROC-AUC |
| 908,100,280,90 | Card | kpi_summary.top20_churn_capture; Max; percentage 2 decimals; title Top-20% capture |
| 32,218,565,220 | Clustered bar | model_comparison.model on Y, average_precision on X, Max; X axis 0 to 1; title Compare risk rankings |
| 623,218,565,220 | Clustered bar | shap_attribution.feature on Y, mean_abs_shap on X, Max; descending; title What shapes the score |
| 32,464,565,220 | Line | scenario_sensitivity.preventable_fraction on X (percentage), expected_net_units on Y (Max); title Test the offer assumption |
| 623,464,565,220 | Clustered column | segment_summary.segment categorical X, observed_churn_rate Y (Max; percentage; axis 0 to 1); customers tooltip; title Churn across segments |
| 32,712,1156,190 | Table | holdout_decisions customer_id, risk, segment, scenario_value, scenario_cost, selected; risk descending; title Holdout decision queue |

Keep the one-row KPI values disconnected from the table. `selected` is the fixed
1,000-unit/20%-effect benchmark, not a dynamic optimization measure in Power BI.
The sensitivity curve is the existing pipeline benchmark. No DAX slider can
claim to re-run the MILP unless an implementation is separately built/tested.
SHAP is from a separate training-only random forest, not the calibrated winner.
Scenario value/cost/net are hypothetical units, never observed money or savings.


## 3. Finish and inspect

1. Add a small footer below the table: `Research prototype. Frozen holdout.
   No live deployment. See repository limitations.` Keep all content on one page.
2. Compare the four cards to `kpi_summary.csv` and the repository screenshot.
   Check chart totals and table row counts. The charts plus table are five
   visuals, excluding the four KPI cards.
3. Test table sorting and confirm it does not filter the KPI summaries. Do not
   add slicers that make holdout results look like live customer predictions.
4. Save as `RetentionLab.pbix` locally. Do not Publish, enable automatic refresh or
   upload data to a workspace while the deployment gate remains closed.
5. For mobile, use View > Mobile layout and stack the same cards/charts. Native
   Power BI mobile behavior must be inspected on the resulting report; this kit
   does not claim that step is already done.

## Troubleshooting and boundaries

- Theme command names vary by Desktop release; choose the custom JSON import,
  not a marketplace visual. Basic theme keys are used to avoid version-specific
  visual schemas. Manual formatting above is still required.
- This kit does not include a generated .pbix, DAX optimization engine, gateways,
  scheduled refresh, Power BI service workspace or paid license.
- Source CSVs are derived from the checked-in frozen evidence. Re-export only
  through `python scripts/export_powerbi.py`; inspect diffs before replacement.
- Power BI service also has browser report-authoring routes, subject to account,
  license and tenant capability. Desktop is the chosen route for this kit, not
  a claim that browser authoring is impossible.

## Official references

- https://learn.microsoft.com/en-us/power-bi/connect-data/desktop-connect-csv
- https://learn.microsoft.com/en-us/power-bi/create-reports/desktop-report-themes
- https://learn.microsoft.com/en-us/power-bi/create-reports/service-quick-create-report
