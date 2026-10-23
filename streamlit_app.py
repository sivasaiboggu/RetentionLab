"""Artifact-only Streamlit decision dashboard. No model training or cloud writes."""

from pathlib import Path
import json
import sys
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
from retentionlab.optimization import optimize_targets

NAVY, ORANGE, WHITE = "#0B1F33", "#FF5A1F", "#FFFFFF"
st.set_page_config(
    page_title="RetentionLab | Decision workbench", page_icon="📊", layout="wide"
)


st.html(
    """<style>
[data-testid="stMetric"]{background:#13304D;border-top:3px solid #FF5A1F;border-radius:8px;padding:16px}
[data-testid="stAlert"]{background:#13304D;color:#FFFFFF;border-left:3px solid #FF5A1F}
[data-testid="stAlert"] p,[data-testid="stAlert"] svg{color:#FFFFFF!important;fill:#FFFFFF}
</style>"""
)


def chart(fig):
    fig.update_layout(
        template="plotly_dark",
        title_font_size=20,
        paper_bgcolor=NAVY,
        plot_bgcolor=NAVY,
        font_color=WHITE,
        margin=dict(l=12, r=12, t=66, b=24),
        colorway=[ORANGE, WHITE],
        height=360,
    )
    st.plotly_chart(
        fig, use_container_width=True, theme=None, config={"displayModeBar": False}
    )


@st.cache_data
def artifacts():
    result = json.loads((ROOT / "artifacts/results.json").read_text())
    rows = pd.read_csv(ROOT / "artifacts/holdout_scores.csv")
    return result, rows


st.caption("RETENTIONLAB / BUDGET-AWARE CHURN DECISIONS")
st.title("Predict risk. Plan the next decision.")
st.write("One operator. Nine months of behavior. A three-month planning gap.")
st.write(
    "Research portfolio, not a live customer system. Scenario values are hypothetical units, not actual savings or currency. No offers are sent."
)
try:
    result, rows = artifacts()
except (OSError, ValueError) as error:
    st.error("Artifacts are unavailable. Run the pipeline from the README first.")
    st.stop()
selected_model = result["selected_model"]
measured = result["models"][selected_model]["holdout"]
cols = st.columns(4)
for col, title, value in zip(
    cols,
    [
        "Source customers",
        "Holdout average precision",
        "Holdout ROC-AUC",
        "Top-20% churn capture",
    ],
    [
        f"{result['rows']:,}",
        f"{measured['average_precision']:.3f}",
        f"{measured['roc_auc']:.3f}",
        f"{100 * result['holdout_top_20_percent_churn_capture']:.2f}%",
    ],
):
    col.metric(title, value)
st.caption(
    "Metrics stay frozen: 620-row grouped holdout, 80 churners. Models and thresholds were selected on validation, not holdout."
)

left, right = st.columns(2)
with left:
    comparison = pd.DataFrame(
        [
            {
                "Model": name.replace("_", " "),
                "Average precision": values["holdout"]["average_precision"],
            }
            for name, values in result["models"].items()
        ]
    )
    chart(
        px.bar(
            comparison,
            x="Average precision",
            y="Model",
            orientation="h",
            title="Risk ranking beats<br>the prior baseline",
            color_discrete_sequence=[ORANGE],
            range_x=[0, 1],
        )
    )
    st.caption(
        "Shown: holdout AP. Validation AP selected XGBoost. Random forest has better holdout F1; no winner was reselected afterward."
    )
with right:
    importance = pd.DataFrame(result["shap"][:6]).rename(
        columns={"feature": "Feature", "mean_abs_shap": "Mean absolute SHAP"}
    )
    chart(
        px.bar(
            importance,
            x="Mean absolute SHAP",
            y="Feature",
            orientation="h",
            title="Complaints lead<br>tree attribution",
            color_discrete_sequence=[ORANGE],
        )
    )
    st.caption(
        "Separate training-only random forest, 100 validation rows. Not the calibrated winner and not causal drivers."
    )

st.subheader("Explore a retention scenario")
a, b, c = st.columns(3)
with a:
    budget = st.number_input(
        "Budget (hypothetical units)", min_value=0, max_value=5000, value=1000, step=50
    )
with b:
    preventable = st.slider(
        "Assumed preventable churn (%)", min_value=0, max_value=100, value=20, step=5
    )
with c:
    segment = st.selectbox(
        "Decision-queue segment",
        ["All segments"] + [str(x) for x in sorted(rows.segment.unique())],
    )
try:
    contact, net = optimize_targets(
        rows.risk, rows.scenario_value, rows.scenario_cost, budget, preventable / 100
    )
except (ValueError, RuntimeError):
    st.error(
        "The scenario could not be solved within the configured limits. No contact plan was produced."
    )
    st.stop()
st.write(
    f'{int(contact.sum())} contacts selected; {rows.loc[contact, "scenario_cost"].sum():,.0f} of {budget:,} units spent; {net:,.1f} expected net hypothetical units.'
)
st.caption(
    "Assumptions: value = 500 + 100 × charge band; cost = 10 + 2 × charge band. No treatment data exists: this is not causal uplift or measured ROI. Segment filtering below does not change the optimization population."
)
left, right = st.columns(2)
with left:
    sensitivity = pd.DataFrame(
        [
            {
                "Preventable churn (%)": x["preventable_fraction"] * 100,
                "Expected net units": x["expected_net_units"],
            }
            for x in result["scenario"]["sensitivity"]
        ]
    )
    chart(
        px.line(
            sensitivity,
            x="Preventable churn (%)",
            y="Expected net units",
            markers=True,
            title="Value depends on<br>assumed offer effect",
            color_discrete_sequence=[ORANGE],
        )
    )
    st.caption(
        "Fixed pipeline sensitivity at the 1,000-unit benchmark budget; not the interactive budget above."
    )
with right:
    segment_summary = rows.groupby("segment", as_index=False).agg(
        churn_rate=("churn", "mean"), customers=("customer_id", "count")
    )
    segment_summary["Observed churn (%)"] = segment_summary.churn_rate * 100
    segment_summary["Segment"] = segment_summary.segment.astype(str)
    chart(
        px.bar(
            segment_summary,
            x="Segment",
            y="Observed churn (%)",
            hover_data=["customers"],
            title="Observed churn varies<br>by segment",
            color_discrete_sequence=[ORANGE],
            range_y=[0, 100],
        )
    )
    st.caption(
        "Training-fitted K-Means segments; holdout outcomes shown for retrospective analysis, not available at decision time."
    )

st.subheader("Holdout decision queue")
queue = rows.assign(budget_selected=contact).sort_values("risk", ascending=False)
if segment != "All segments":
    queue = queue[queue.segment.astype(str) == segment]
selected_only = st.checkbox("Show budget-selected contacts only")
if selected_only:
    queue = queue[queue.budget_selected]
st.dataframe(
    queue[
        [
            "customer_id",
            "risk",
            "segment",
            "scenario_value",
            "scenario_cost",
            "budget_selected",
        ]
    ],
    hide_index=True,
    width="stretch",
    column_config={
        "risk": st.column_config.NumberColumn("Predicted churn risk", format="%.3f")
    },
)
st.download_button(
    "Download filtered scenario CSV",
    queue[
        [
            "customer_id",
            "risk",
            "segment",
            "scenario_value",
            "scenario_cost",
            "budget_selected",
        ]
    ].to_csv(index=False),
    "retention-scenario.csv",
    "text/csv",
)
with st.expander("Data boundaries, methods and provenance"):
    st.write(
        "UCI Iranian Churn, CC BY 4.0. Status, age and undocumented Customer Value are excluded from predictors. Identical observable feature profiles stay in one outer split and inner calibration fold. Training-only association tests and SHAP are not causal evidence. No transaction dates, actual revenue or offer outcomes exist. External-market validity is untested."
    )
    st.link_button(
        "UCI dataset and citation",
        "https://archive.ics.uci.edu/dataset/563/iranian+churn+dataset",
    )
st.caption(
    "Streamlit + Plotly Express / artifact-only local app / no public deployment"
)
