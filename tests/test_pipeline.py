import itertools
import unittest
import numpy as np
from retentionlab.optimization import optimize_targets
from retentionlab.pipeline import load_features, grouped_split, FEATURES


class PipelineTests(unittest.TestCase):
    def test_sql_rows_and_types(self):
        d = load_features()
        self.assertEqual(len(d), 3150)
        self.assertFalse(d[FEATURES].isna().any().any())
        self.assertEqual(set(d.plan_name), {"Pay as you go", "Contractual"})
        self.assertNotIn("Status", FEATURES)
        self.assertNotIn("Customer Value", FEATURES)

    def test_group_split_no_overlap_and_complete(self):
        d = load_features()
        a, b, c, g = grouped_split(d)
        self.assertEqual(len(set(a) | set(b) | set(c)), len(d))
        for x, y in [(a, b), (b, c), (a, c)]:
            self.assertFalse(set(g[x]) & set(g[y]))

    def test_optimizer_matches_brute_force(self):
        r = np.array([0.2, 0.8, 0.7, 0.4])
        v = np.array([200, 100, 200, 300])
        c = np.array([10, 15, 20, 10])
        budget = 30
        selected, net = optimize_targets(r, v, c, budget)
        expected = max(
            sum((r * 0.2 * v - c) * bits)
            for bits in itertools.product([0, 1], repeat=4)
            if sum(c * bits) <= budget
        )
        self.assertAlmostEqual(net, expected)
        self.assertLessEqual(sum(c[selected]), budget)

    def test_zero_uplift_selects_no_one(self):
        selected, net = optimize_targets([0.9], [100], [5], 100, 0)
        self.assertFalse(selected.any())
        self.assertEqual(net, 0)

    def test_empty_budget_and_negative_value(self):
        self.assertEqual(optimize_targets([0.8], [100], [10], 0)[1], 0)
        self.assertEqual(optimize_targets([0], [100], [10], 100)[1], 0)

    def test_invalid_inputs(self):
        for args in [
            ([2], [1], [1], 10),
            ([0.5], [1], [0], 10),
            ([0.5], [1], [1], -1),
            ([float("nan")], [1], [1], 10),
            ([0.5, 0.2], [1], [1], 10),
        ]:
            with self.assertRaises(ValueError):
                optimize_targets(*args)
