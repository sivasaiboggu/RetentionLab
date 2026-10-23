"""Export a local Power BI build kit from checked frozen dashboard evidence."""
from pathlib import Path
import json,hashlib
import pandas as pd
import sys
THEME={"name":"Graphite Sage Ivory", "dataColors":["#A8C4A2","#F3F0E7","#52655C"],"background":"#151D21","foreground":"#F3F0E7","tableAccent":"#A8C4A2"}
for name in ['RetentionLab']:
 root=Path(__file__).resolve().parents[1];out=root/'powerbi';out.mkdir(exist_ok=True)
 sys.path.insert(0, str(root / 'src'))
 from retentionlab.evidence import verify_bundle
 verify_bundle(root)
 d=json.load(open(root/'artifacts/results.json'))
 (out/'graphite-sage-theme.json').write_text(json.dumps(THEME,indent=2)+'\n')
 pd.DataFrame([{'model':model,'selected_on_validation':model==d['selected_model'],**value['holdout']} for model,value in d['models'].items()]).drop(columns=['confusion_matrix']).to_csv(out/'model_comparison.csv',index=False)
 if name=='RetentionLab':
  rows=pd.read_csv(root/'artifacts/holdout_scores.csv');rows[['customer_id','risk','churn','segment','scenario_value','scenario_cost','selected']].to_csv(out/'holdout_decisions.csv',index=False)
  m=d['models'][d['selected_model']]['holdout']
  pd.DataFrame([{'source_customers':d['rows'],'holdout_average_precision':m['average_precision'],'holdout_roc_auc':m['roc_auc'],'top20_churn_capture':d['holdout_top_20_percent_churn_capture']}]).to_csv(out/'kpi_summary.csv',index=False)
  pd.DataFrame(d['shap'][:6]).to_csv(out/'shap_attribution.csv',index=False)
  pd.DataFrame(d['scenario']['sensitivity']).to_csv(out/'scenario_sensitivity.csv',index=False)
  rows.groupby('segment',as_index=False).agg(observed_churn_rate=('churn','mean'),customers=('customer_id','count')).to_csv(out/'segment_summary.csv',index=False)
  protocol='''## Fields and visuals

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
'''
 else:
  rows=pd.DataFrame(json.load(open(root/'artifacts/queue.json')))
  rows[['review_id','text','predicted_sentiment','confidence','sentiment_needs_review','category','topic','review_status']].to_csv(out/'review_queue.csv',index=False)
  m=d['models'][d['selected_model']]['holdout'];p=d['review_policy']
  pd.DataFrame([{'unique_sentences':d['clean_rows'],'holdout_sentiment_accuracy':m['accuracy'],'holdout_macro_f1':m['macro_f1'],'new_human_issue_labels':0}]).to_csv(out/'kpi_summary.csv',index=False)
  pd.DataFrame([{'reference':ref,'prediction':pred,'rows':m['confusion_matrix'][i][j]} for i,ref in enumerate(['negative','positive']) for j,pred in enumerate(['negative','positive'])]).to_csv(out/'confusion_matrix.csv',index=False)
  pd.DataFrame([{'decision':'Accepted','rows':p['holdout_accepted']},{'decision':'Needs review','rows':200-p['holdout_accepted']}]).to_csv(out/'review_routing.csv',index=False)
  rows.category.value_counts().rename_axis('issue_proposal').reset_index(name='rows').to_csv(out/'issue_counts.csv',index=False)
  protocol='''## Fields and visuals

Do not auto-create relationships. Summary tables must remain disconnected, so
filtering the queue never rewrites fixed evaluation metrics.

| Position (x,y,width,height) | Visual | Fields and exact settings |
|---|---|---|
| 32,100,280,90 | Card | kpi_summary.unique_sentences; Max; whole number; title Unique sentences |
| 324,100,280,90 | Card | kpi_summary.holdout_sentiment_accuracy; Max; percentage 1 decimal; title Holdout accuracy |
| 616,100,280,90 | Card | kpi_summary.holdout_macro_f1; Max; 3 decimals; title Holdout macro-F1 |
| 908,100,280,90 | Card | kpi_summary.new_human_issue_labels; Max; whole number; title New human issue labels |
| 32,218,565,220 | Clustered column | model_comparison.model X, accuracy Y (Max; percentage, axis 0 to 1); title Sentiment accuracy |
| 623,218,565,220 | Matrix | confusion_matrix.reference Rows, prediction Columns, rows Values (Sum); conditional background sage scale; title Where predictions miss |
| 32,464,565,220 | Clustered bar | review_routing.decision Y, rows X (Max), X axis 0 to 200; title What goes to review |
| 623,464,565,220 | Clustered bar | issue_counts.issue_proposal Y, rows X (Max), descending; title Proposed issue signals |
| 32,712,1156,190 | Table | review_queue review_id, text, predicted_sentiment, confidence, category, topic, review_status; confidence ascending; title Review queue |

The confusion matrix uses publisher reference labels, not new human work.
Accepted = 140/200 with 124 correct (88.57%), below the 90% validation target.
All issue proposals remain unvalidated and require independent review. These
CSV exports include predictions for analysis. Never use review_queue as the
blind annotation source; the separate original blind_rows artifact has IDs/text
only. New human issue labels remain zero. There are no dates/revenue to plot.
'''
 guide=f'''# {name}: Power BI Desktop build kit

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
3. Add a text header at (32,24): `{name}` in Segoe UI Semibold 26pt,
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

{protocol}

## 3. Finish and inspect

1. Add a small footer below the table: `Research prototype. Frozen holdout.
   No live deployment. See repository limitations.` Keep all content on one page.
2. Compare the four cards to `kpi_summary.csv` and the repository screenshot.
   Check chart totals and table row counts. The charts plus table are five
   visuals, excluding the four KPI cards.
3. Test table sorting and confirm it does not filter the KPI summaries. Do not
   add slicers that make holdout results look like live customer predictions.
4. Save as `{name}.pbix` locally. Do not Publish, enable automatic refresh or
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
'''
 (out/'BUILD_GUIDE.md').write_text(guide)
 manifest={p.name:{'rows':len(pd.read_csv(p)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in out.glob('*.csv')}
 (out/'exports_manifest.json').write_text(json.dumps({'source':'../artifacts/ frozen bundle','exports':manifest,'status':'build kit; not a rendered PBIX'},indent=2)+'\n')
