/* Exact integer-cost knapsack for a transparent browser-only scenario.
   This does not replace the pipeline's SciPy MILP or estimate treatment effects. */
export function solveScenario(rows, budget, preventable) {
  if (
    !Number.isInteger(budget) ||
    budget < 0 ||
    budget > 5000 ||
    !Number.isFinite(preventable) ||
    preventable < 0 ||
    preventable > 1
  )
    throw new Error(
      "Use a whole-unit budget from 0 to 5000 and a preventable fraction from 0 to 1.",
    );
  const dp = new Float64Array(budget + 1);
  const choices = Array.from(
    { length: rows.length },
    () => new Uint8Array(budget + 1),
  );
  rows.forEach((row, index) => {
    const cost = row.scenario_cost,
      net = row.risk * preventable * row.scenario_value - cost;
    if (!Number.isInteger(cost) || cost <= 0 || !Number.isFinite(net))
      throw new Error("Invalid scenario row.");
    if (net <= 0) return;
    for (let b = budget; b >= cost; b--) {
      const candidate = dp[b - cost] + net;
      if (candidate > dp[b] + 1e-10) {
        dp[b] = candidate;
        choices[index][b] = 1;
      }
    }
  });
  let remaining = budget;
  const selected = [];
  for (let i = rows.length - 1; i >= 0; i--) {
    if (choices[i][remaining]) {
      selected.push(rows[i].customer_id);
      remaining -= rows[i].scenario_cost;
    }
  }
  return { selected, spend: budget - remaining, net: dp[budget] };
}
