"""Rebuild audited SQLite features, grouped evaluation and scenario artifacts."""

from pathlib import Path
import hashlib
import json
import sqlite3
import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, ttest_ind
from sklearn.calibration import CalibratedClassifierCV
from sklearn.cluster import KMeans
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    roc_auc_score,
    precision_score,
    recall_score,
    f1_score,
    brier_score_loss,
    confusion_matrix,
)
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier
from .optimization import optimize_targets

ROOT = Path(__file__).resolve().parents[2]
FEATURES = [
    "call_failures",
    "complaint",
    "tenure_months",
    "charge_band",
    "usage_seconds",
    "call_count",
    "sms_count",
    "contacts",
    "tariff_plan",
    "failure_rate",
    "seconds_per_call",
]


def load_features(root=ROOT):
    raw = pd.read_csv(root / "data/raw.csv")
    if raw.isna().any().any() or not set(raw.Churn.unique()) <= {0, 1}:
        raise ValueError("Source has missing or invalid target values")
    connection = sqlite3.connect(root / "data/retention.db")
    raw.to_sql("raw", connection, if_exists="replace", index=False)
    pd.DataFrame(
        {"tariff_plan": [1, 2], "plan_name": ["Pay as you go", "Contractual"]}
    ).to_sql("tariff_lookup", connection, if_exists="replace", index=False)
    connection.execute("DROP TABLE IF EXISTS features")
    connection.executescript((root / "sql/features.sql").read_text())
    data = pd.read_sql("SELECT * FROM features ORDER BY customer_id", connection)
    connection.close()
    if len(data) != len(raw) or data[FEATURES].isna().any().any():
        raise ValueError("Feature join lost rows or introduced missing data")
    return data


def grouped_split(data):
    groups = pd.util.hash_pandas_object(data[FEATURES], index=False).values
    y = data.churn.to_numpy()
    trainval, test = next(
        StratifiedGroupKFold(5, shuffle=True, random_state=42).split(data, y, groups)
    )
    a, b = next(
        StratifiedGroupKFold(4, shuffle=True, random_state=43).split(
            data.iloc[trainval], y[trainval], groups[trainval]
        )
    )
    train, val = trainval[a], trainval[b]
    for left, right in [(train, val), (train, test), (val, test)]:
        assert not set(groups[left]) & set(groups[right])
    return train, val, test, groups


def metrics(y, p, threshold):
    pred = p >= threshold
    return {
        "roc_auc": float(roc_auc_score(y, p)),
        "average_precision": float(average_precision_score(y, p)),
        "precision": float(precision_score(y, pred, zero_division=0)),
        "recall": float(recall_score(y, pred)),
        "f1": float(f1_score(y, pred)),
        "brier": float(brier_score_loss(y, p)),
        "confusion_matrix": confusion_matrix(y, pred).tolist(),
    }


def run(root=ROOT):
    data = load_features(root)
    train, val, test, groups = grouped_split(data)
    X, y = data[FEATURES], data.churn
    ratio = float((y.iloc[train] == 0).sum() / y.iloc[train].sum())
    candidates = {
        "prior_baseline": DummyClassifier(strategy="prior"),
        "logistic_regression": make_pipeline(
            StandardScaler(),
            LogisticRegression(class_weight="balanced", max_iter=1500, random_state=42),
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=180,
            min_samples_leaf=5,
            class_weight="balanced",
            random_state=42,
            n_jobs=2,
        ),
        "xgboost": XGBClassifier(
            n_estimators=150,
            max_depth=3,
            learning_rate=0.05,
            subsample=0.9,
            colsample_bytree=0.9,
            scale_pos_weight=ratio,
            random_state=42,
            n_jobs=2,
        ),
    }
    # Calibration folds are group-separated too; repeated feature profiles never leak.
    cv = list(
        StratifiedGroupKFold(3, shuffle=True, random_state=44).split(
            X.iloc[train], y.iloc[train], groups[train]
        )
    )
    models, scores = {}, {}
    for name, estimator in candidates.items():
        model = CalibratedClassifierCV(estimator, cv=cv, method="sigmoid")
        model.fit(X.iloc[train], y.iloc[train])
        pv = model.predict_proba(X.iloc[val])[:, 1]
        thresholds = np.linspace(0.05, 0.95, 91)
        threshold = float(max(thresholds, key=lambda t: f1_score(y.iloc[val], pv >= t)))
        scores[name] = {
            "threshold": threshold,
            "validation": metrics(y.iloc[val], pv, threshold),
        }
        models[name] = model
    winner = max(
        (n for n in candidates if n != "prior_baseline"),
        key=lambda n: scores[n]["validation"]["average_precision"],
    )
    for name, model in models.items():
        scores[name]["holdout"] = metrics(
            y.iloc[test],
            model.predict_proba(X.iloc[test])[:, 1],
            scores[name]["threshold"],
        )
    risk = models[winner].predict_proba(X.iloc[test])[:, 1]
    scored = data.iloc[test].copy()
    scored["risk"] = risk
    # Monetary units are synthetic assumptions, not source Customer Value or currency.
    scored["scenario_value"] = 500 + 100 * scored.charge_band
    scored["scenario_cost"] = 10 + 2 * scored.charge_band
    budget = 1000
    selected, net = optimize_targets(
        risk, scored.scenario_value, scored.scenario_cost, budget
    )
    scored["selected"] = selected
    scaler = StandardScaler().fit(X.iloc[train])
    cluster = KMeans(n_clusters=4, random_state=42, n_init=10).fit(
        scaler.transform(X.iloc[train])
    )
    scored["segment"] = cluster.predict(scaler.transform(X.iloc[test]))
    ranked = np.argsort(-risk)[: int(np.ceil(0.2 * len(test)))]
    top_capture = float(y.iloc[test].to_numpy()[ranked].sum() / y.iloc[test].sum())
    # Association tests on training data only, not causal evidence.
    table = pd.crosstab(data.iloc[train].complaint, y.iloc[train])
    chi = chi2_contingency(table)
    welch = ttest_ind(
        data.iloc[train].loc[y.iloc[train] == 1, "usage_seconds"],
        data.iloc[train].loc[y.iloc[train] == 0, "usage_seconds"],
        equal_var=False,
    )
    # Explain a separate training-only tree, not the calibrated ensemble's output.
    import shap

    explain_model = candidates["random_forest"].fit(X.iloc[train], y.iloc[train])
    explanation = shap.TreeExplainer(explain_model).shap_values(X.iloc[val].head(100))
    values = np.asarray(explanation)
    if values.ndim == 3:
        values = values[:, :, 1]
    importance = sorted(
        [
            {"feature": f, "mean_abs_shap": float(v)}
            for f, v in zip(FEATURES, np.abs(values).mean(axis=0))
        ],
        key=lambda x: -x["mean_abs_shap"],
    )
    result = {
        "dataset": "UCI Iranian Churn",
        "raw_sha256": hashlib.sha256((root / "data/raw.csv").read_bytes()).hexdigest(),
        "rows": len(data),
        "duplicate_feature_profiles": int(pd.Series(groups).duplicated().sum()),
        "splits": {
            name: {"rows": len(idx), "churn_rate": float(y.iloc[idx].mean())}
            for name, idx in [("train", train), ("validation", val), ("holdout", test)]
        },
        "selection_metric": "validation average precision",
        "selected_model": winner,
        "models": scores,
        "holdout_top_20_percent_churn_capture": top_capture,
        "training_associations": {
            "complaint_chi_square": float(chi.statistic),
            "complaint_p_value": float(chi.pvalue),
            "usage_welch_t": float(welch.statistic),
            "usage_p_value": float(welch.pvalue),
        },
        "scenario": {
            "budget": budget,
            "spend": float(scored.loc[selected, "scenario_cost"].sum()),
            "selected": int(selected.sum()),
            "expected_net_units": net,
            "preventable_fraction_assumed": 0.2,
            "observed_savings": None,
            "units": "hypothetical monetary units; not INR/USD",
            "sensitivity": [
                {
                    "preventable_fraction": a,
                    "expected_net_units": optimize_targets(
                        risk, scored.scenario_value, scored.scenario_cost, budget, a
                    )[1],
                }
                for a in [0, 0.1, 0.2, 0.3]
            ],
        },
        "explanation_model": "separate training-only random forest; not calibrated winner",
        "shap": importance,
    }
    (root / "artifacts").mkdir(exist_ok=True)
    (root / "artifacts/results.json").write_text(
        json.dumps(result, indent=2, allow_nan=False) + "\n"
    )
    scored.to_csv(root / "artifacts/holdout_scores.csv", index=False)
    scored.sort_values("risk", ascending=False)[
        [
            "customer_id",
            "risk",
            "segment",
            "scenario_value",
            "scenario_cost",
            "selected",
        ]
    ].to_json(root / "artifacts/queue.json", orient="records", indent=2)
    (root / "artifacts/splits.json").write_text(
        json.dumps(
            {
                n: data.iloc[i].customer_id.tolist()
                for n, i in [("train", train), ("validation", val), ("holdout", test)]
            }
        )
    )
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    run()
