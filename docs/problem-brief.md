# RetentionLab: a decision, not an accuracy contest

An analyst has a fixed contact budget. Which customers should receive a
retention offer, and when is contacting nobody the better decision?

**Prediction target:** churn at the end of month 12 using nine-month aggregates.
**Hypotheses:** complaints and lower usage are associated with later churn.
Tests run on training rows only. Association does not imply an effective remedy.
**Primary model-selection metric:** validation average precision, because churn
is a minority outcome. Thresholds maximize validation F1, not holdout F1.
**Business KPI:** expected net scenario value under budget, with sensitivity to
an explicitly assumed preventable fraction. Observed savings are unavailable.

This dataset has no randomized offer, intervention cost, currency, actual
revenue, or transaction dates. The project cannot estimate causal uplift, RFM
recency, lifetime value or realized retention ROI. A next-stage experiment would
randomize an approved offer within risk bands, log costs and outcomes, and
estimate heterogeneous treatment effects on a pre-registered holdout.

Identical observable feature profiles remain in the same split. Demographics,
Status and the undocumented Customer Value formula are excluded from modeling.
The source is one Iranian telecom operator, not a retail/banking or Indian
market sample. No conclusions about those populations are claimed.
