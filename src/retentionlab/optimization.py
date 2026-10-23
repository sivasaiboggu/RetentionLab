"""Budget-constrained scenario planning, never a causal uplift estimator."""

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp


def optimize_targets(risk, value, cost, budget, preventable_fraction=0.2):
    risk, value, cost = [np.asarray(x, dtype=float) for x in (risk, value, cost)]
    if not (
        risk.ndim == value.ndim == cost.ndim == 1
        and len(risk) == len(value) == len(cost)
    ):
        raise ValueError("Inputs must be equally sized one-dimensional arrays")
    if not all(np.isfinite(x).all() for x in (risk, value, cost)) or not np.isfinite(
        budget
    ):
        raise ValueError("Inputs must be finite")
    if (
        ((risk < 0) | (risk > 1)).any()
        or (value < 0).any()
        or (cost <= 0).any()
        or budget < 0
        or not 0 <= preventable_fraction <= 1
    ):
        raise ValueError("Invalid scenario assumptions")
    net = risk * preventable_fraction * value - cost
    if len(risk) == 0:
        return np.array([], dtype=bool), 0.0
    result = milp(
        -net,
        integrality=np.ones(len(net)),
        bounds=Bounds(0, 1),
        constraints=LinearConstraint(cost, -np.inf, budget),
        options={"time_limit": 30, "mip_rel_gap": 1e-6},
    )
    if not result.success:
        raise RuntimeError(f"Optimization did not reach an optimum: {result.message}")
    selected = result.x > 0.5
    if cost[selected].sum() > budget + 1e-6:
        raise RuntimeError("Solver returned an infeasible budget")
    return selected, float(net[selected].sum())
