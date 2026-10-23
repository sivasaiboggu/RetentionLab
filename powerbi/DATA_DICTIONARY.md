# Export data dictionary

These are disconnected analysis tables, not a relational operational model.
Fractions stay 0-1 and should be formatted as percentages, not multiplied.

## holdout_decisions.csv

Rows: 620. UTF-8 with header.

| Column | CSV-inferred type | Power BI treatment |
|---|---|---|
| customer_id | int64 | Whole Number / categorical, do not summarize |
| risk | float64 | Decimal Number / Max for precomputed metrics |
| churn | int64 | Decimal Number / Max for precomputed metrics |
| segment | int64 | Whole Number / categorical, do not summarize |
| scenario_value | int64 | Decimal Number / Max for precomputed metrics |
| scenario_cost | int64 | Decimal Number / Max for precomputed metrics |
| selected | bool | True/False |

## kpi_summary.csv

Rows: 1. UTF-8 with header.

| Column | CSV-inferred type | Power BI treatment |
|---|---|---|
| source_customers | int64 | Whole Number; Max for one-row summary, Sum only for disjoint counts |
| holdout_average_precision | float64 | Decimal Number / Max for precomputed metrics |
| holdout_roc_auc | float64 | Decimal Number / Max for precomputed metrics |
| top20_churn_capture | float64 | Decimal Number / Max for precomputed metrics |

## model_comparison.csv

Rows: 4. UTF-8 with header.

| Column | CSV-inferred type | Power BI treatment |
|---|---|---|
| model | object | Text / do not summarize |
| selected_on_validation | bool | True/False |
| roc_auc | float64 | Decimal Number / Max for precomputed metrics |
| average_precision | float64 | Decimal Number / Max for precomputed metrics |
| precision | float64 | Decimal Number / Max for precomputed metrics |
| recall | float64 | Decimal Number / Max for precomputed metrics |
| f1 | float64 | Decimal Number / Max for precomputed metrics |
| brier | float64 | Decimal Number / Max for precomputed metrics |

## scenario_sensitivity.csv

Rows: 4. UTF-8 with header.

| Column | CSV-inferred type | Power BI treatment |
|---|---|---|
| preventable_fraction | float64 | Decimal Number / Max for precomputed metrics |
| expected_net_units | float64 | Decimal Number / Max for precomputed metrics |

## segment_summary.csv

Rows: 4. UTF-8 with header.

| Column | CSV-inferred type | Power BI treatment |
|---|---|---|
| segment | int64 | Whole Number / categorical, do not summarize |
| observed_churn_rate | float64 | Decimal Number / Max for precomputed metrics |
| customers | int64 | Whole Number; Max for one-row summary, Sum only for disjoint counts |

## shap_attribution.csv

Rows: 6. UTF-8 with header.

| Column | CSV-inferred type | Power BI treatment |
|---|---|---|
| feature | object | Text / do not summarize |
| mean_abs_shap | float64 | Decimal Number / Max for precomputed metrics |

## Interpretation limits

IDs are dataset row identifiers, not identities to contact. Risk/confidence are model outputs.
Summary tables report frozen evaluation, not live performance. Any scenario value is hypothetical.
Feedback issue categories and topics are unvalidated proposals, not human labels.
