"""Budget-constrained scenario planning, never a causal uplift estimator."""

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp


def optimize_targets(risk, value, cost, budget, preventable_fraction=0.2):
    if np.ndim(budget) != 0 or np.ndim(preventable_fraction) != 0:
        raise ValueError("Budget and preventable fraction must be scalars")
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
    with np.errstate(over="ignore", invalid="ignore"):
        net = risk * preventable_fraction * value - cost
    if not np.isfinite(net).all():
        raise ValueError("Scenario values exceed the supported numeric range")
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
        raise RuntimeError("Optimization did not reach an optimum. No target plan was produced.")
    solution = np.asarray(result.x, dtype=float)
    if solution.shape != net.shape or not np.isfinite(solution).all() or not np.isclose(solution, np.round(solution), atol=1e-6).all() or ((solution < -1e-6) | (solution > 1 + 1e-6)).any():
        raise RuntimeError("Solver returned an invalid target plan")
    selected = solution > 0.5
    if cost[selected].sum() > budget + 1e-6:
        raise RuntimeError("Solver returned an infeasible budget")
    return selected, float(net[selected].sum())
