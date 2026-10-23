import unittest
from genlayer_stub import load_contract_module

m = load_contract_module()

CFG = {
    "sources": [{}, {}, {}, {}],
    "tolerance_bps": 100, "drift_bps": 50, "min_sources": 3, "min_agree": 2,
}


class ToScaled(unittest.TestCase):
    def test_numbers(self):
        self.assertEqual(m.to_scaled(1, 2), 100)
        self.assertEqual(m.to_scaled(1.5, 2), 150)
        self.assertEqual(m.to_scaled("1,234.567", 2), 123457)   # half-up
        self.assertEqual(m.to_scaled("$99", 0), 99)
        self.assertEqual(m.to_scaled("0.000001", 6), 1)
        self.assertEqual(m.to_scaled(".5", 1), 5)

    def test_rejects(self):
        for bad in (True, None, [], "abc", "-1", -3, "1e5", "1.2.3", float("nan"), float("inf"), ""):
            with self.assertRaises(Exception, msg=repr(bad)):
                m.to_scaled(bad, 2)


class Paths(unittest.TestCase):
    def test_path(self):
        self.assertEqual(m.extract_json_path({"a": {"b": [1, {"c": 7}]}}, "a.b.1.c"), 7)
        with self.assertRaises(Exception):
            m.extract_json_path({"a": 1}, "a.b")

    def test_wrapped_json(self):
        self.assertEqual(m.parse_json_page('noise {"x": 1} tail'), {"x": 1})
        with self.assertRaises(Exception):
            m.parse_json_page("no json here")


class Reconcile(unittest.TestCase):
    def test_median(self):
        self.assertEqual(m.median_int([3, 1, 2]), 2)
        self.assertEqual(m.median_int([1, 2, 3, 4]), 2)

    def test_ok_with_outlier(self):
        r = m.reconcile_values({0: 10000, 1: 10020, 2: 10010, 3: 20000}, 100, 3, 2)
        self.assertEqual(r["status"], "OK")
        self.assertEqual(r["outliers"], [3])
        self.assertEqual(r["agreeing"], [0, 1, 2])
        self.assertEqual(r["value"], "10010")

    def test_no_quorum(self):
        r = m.reconcile_values({0: 100, 1: 200, 2: 400}, 100, 3, 2)
        self.assertEqual(r["status"], "NO_QUORUM")

    def test_insufficient(self):
        r = m.reconcile_values({0: 100, 1: 100}, 100, 3, 2)
        self.assertEqual(r["status"], "INSUFFICIENT_SOURCES")

    def test_zero_median(self):
        r = m.reconcile_values({0: 0, 1: 0, 2: 5}, 100, 3, 2)
        self.assertEqual(r["status"], "OK")
        self.assertEqual(r["outliers"], [2])


def obs(values, **cfg):
    return m.reconcile_values(values, cfg.get("t", 100), 3, 2) | {
        "failed": [], "values": {str(k): str(v) for k, v in values.items()}}


class Equivalence(unittest.TestCase):
    def test_accepts_small_drift(self):
        leader = obs({0: 10000, 1: 10020, 2: 10010})
        mine = obs({0: 10010, 1: 10015, 2: 10012})
        self.assertTrue(m.is_equivalent(leader, mine, CFG))

    def test_rejects_value_drift(self):
        leader = obs({0: 10000, 1: 10020, 2: 10010})
        mine = obs({0: 10100, 1: 10120, 2: 10110})   # ~1% away > 0.5% drift
        self.assertFalse(m.is_equivalent(leader, mine, CFG))

    def test_rejects_fabricated_source_value(self):
        leader = obs({0: 10000, 1: 10020, 2: 10010})
        mine = obs({0: 10000, 1: 10020, 2: 10010})
        leader["values"]["1"] = "10300"   # leader lies about source 1
        self.assertFalse(m.is_equivalent(leader, mine, CFG))

    def test_rejects_inconsistent_leader(self):
        leader = obs({0: 10000, 1: 10020, 2: 10010})
        mine = obs({0: 10000, 1: 10020, 2: 10010})
        leader["value"] = "10500"         # does not match own median
        self.assertFalse(m.is_equivalent(leader, mine, CFG))

    def test_rejects_status_mismatch(self):
        leader = obs({0: 10000, 1: 10020, 2: 10010})
        mine = obs({0: 100, 1: 5000, 2: 90000})
        self.assertFalse(m.is_equivalent(leader, mine, CFG))

    def test_rejects_unverifiable_quorum(self):
        leader = obs({0: 10000, 1: 10020, 2: 10010})
        mine = obs({0: 10000, 3: 10000, 1: 10020})   # only sources 0,1 overlap -> 2 verified
        mine["values"].pop("3")
        # validator saw just 2 sources of the leader's quorum -> still >= min_agree
        mine2 = {"status": "OK", "value": "10010", "agreeing": [0], "outliers": [],
                 "failed": [1, 2], "values": {"0": "10010"}}
        self.assertFalse(m.is_equivalent(leader, mine2, CFG))  # only 1 verified < 2

    def test_rejects_garbage(self):
        self.assertFalse(m.is_equivalent({}, {}, CFG))


if __name__ == "__main__":
    unittest.main()
