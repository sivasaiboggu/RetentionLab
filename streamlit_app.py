"""Artifact-only Streamlit decision dashboard. No model training or cloud writes."""

from pathlib import Path
import sys
import pandas as pd
import plotly.express as px
import streamlit as st
import altair as alt
from streamlit_extras.metric_cards import style_metric_cards
from streamlit_option_menu import option_menu

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
from retentionlab.optimization import optimize_targets
from retentionlab.evidence import load_dashboard, bundle_fingerprint

CANVAS, ACCENT, TEXT = "#151D21", "#A8C4A2", "#F3F0E7"
st.set_page_config(
    page_title="RetentionLab | Decision workbench", page_icon="📊", layout="wide"
)


st.html("<style>" + (ROOT / "assets/fonts/fonts.css").read_text()
        + (ROOT / "dashboard.css").read_text() + "</style>")


def chart(fig):
    """Use the same neutral/accent system across all Plotly views."""
    fig.update_layout(
        template="plotly_dark",
        title_font_size=20,
        paper_bgcolor="#202B30",
        plot_bgcolor="#202B30",
        font=dict(family="DM Sans, sans-serif", color=TEXT, size=11),
        title=dict(font=dict(family="DM Sans, sans-serif", size=20)),
        margin=dict(l=12, r=12, t=66, b=24),
        colorway=[ACCENT, TEXT],
        height=340,
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(255,255,255,0.07)", zeroline=False)
    fig.update_yaxes(showgrid=False, zeroline=False)
    fig.update_traces(marker_line_width=0, selector=dict(type="bar"))
    st.plotly_chart(
        fig, use_container_width=True, theme=None, config={"displayModeBar": False}
    )


@st.cache_data
def artifacts(fingerprint):
    """A changed bundle cannot reuse a previously checked cache entry."""
    return load_dashboard(ROOT)


st.html('<div class="masthead"><div class="wordmark"><span class="brandmark">r</span>RetentionLab</div><div class="meta">Research workbench / 01</div></div>\n<div class="hero"><div><div class="eyebrow">Customer intelligence / Iranian telecom</div><h1>Know who might leave.<br><em>Decide what comes next.</em></h1><p>A budget-aware view of churn. From risk ranking to a contact plan, with every assumption left in plain sight.</p></div><div class="hero-aside"><div class="meta">The decision window</div><strong>3 months</strong><p>Between the behavior window and the observed churn outcome.</p></div></div>\n<div class="boundary"><b>Research, not a live system.</b><span>Scenario values are hypothetical units, not actual savings or currency. No offers are sent.</span></div>')
try:
    result, rows = artifacts(bundle_fingerprint(ROOT))
except (OSError, ValueError, KeyError, TypeError):
    st.error("Evidence bundle is missing or inconsistent. See the README verification steps.")
    st.stop()
selected_model = result["selected_model"]
measured = result["models"][selected_model]["holdout"]
with st.container(key="kpi-strip"):
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

style_metric_cards(background_color="#202B30", border_color="#35413F",
                   border_left_color="#A8C4A2", border_radius_px=10, box_shadow=False)

st.caption(
    "Metrics stay frozen: 620-row grouped holdout, 80 churners. Models and thresholds were selected on validation, not holdout."
)

st.html('<div class="section-label"><span class="section-num">01 /</span><span>Understand the risk</span></div>')
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
            title="Compare risk rankings",
            color_discrete_sequence=[ACCENT],
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
            title="What shapes the score",
            color_discrete_sequence=[ACCENT],
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
            title="Test the offer assumption",
            color_discrete_sequence=[ACCENT],
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
    segment_chart = alt.Chart(segment_summary).mark_bar(color=ACCENT, cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
        x=alt.X("Segment:N", title="Segment"),
        y=alt.Y("Observed churn (%):Q", scale=alt.Scale(domain=[0, 100])),
        tooltip=["Segment", alt.Tooltip("Observed churn (%):Q", format=".1f"), "customers"],
    ).properties(title="Churn across segments", height=290, padding={"left": 16, "right": 22, "top": 18, "bottom": 14}).configure(
        background="#202B30", font="DM Sans"
    ).configure_axis(labelColor=TEXT, titleColor=TEXT, gridColor="#35413F", domain=False).configure_title(
        color=TEXT, fontSize=20, anchor="start", offset=24
    ).configure_view(strokeOpacity=0)
    st.altair_chart(segment_chart, use_container_width=True, theme=None)

    st.caption(
        "Training-fitted K-Means segments; holdout outcomes shown for retrospective analysis, not available at decision time."
    )

st.subheader("Holdout decision queue")
queue = rows.assign(budget_selected=contact).sort_values("risk", ascending=False)
if segment != "All segments":
    queue = queue[queue.segment.astype(str) == segment]
queue_view = option_menu(None, ["All contacts", "Budget selected"],
    icons=["table", "check2-circle"], orientation="horizontal", key="queue-view",
    styles={"container":{"background-color":"#202B30","padding":"4px","border-radius":"8px"},
            "icon":{"color":"#A8C4A2"}, "nav-link":{"font-size":"13px","color":"#F3F0E7","--hover-color":"#35413F"},
            "nav-link-selected":{"background-color":"#35413F","color":"#F3F0E7"}})
if queue_view == "Budget selected":
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
st.html('<div class="footer"><span>RetentionLab / Research edition</span><span>Frozen evidence · Local workspace · No deployment</span></div>')
