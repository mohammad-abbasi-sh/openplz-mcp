"""Live tests — hit the real OpenPLZ API. Cautious: few requests.

Run:  pytest tests/test_live.py -v
Skip: pytest -m "not live"  (or set OPENPLZ_SKIP_LIVE=1)
"""
import json
import os
import pathlib
import sys
import unittest

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from openplz_mcp import server as srv  # noqa: E402

pytestmark = pytest.mark.live
SKIP = os.environ.get("OPENPLZ_SKIP_LIVE") == "1"


@pytest.mark.skipif(SKIP, reason="OPENPLZ_SKIP_LIVE=1")
class TestLive(unittest.TestCase):
    def test_lookup_postal_code_live(self):
        out = json.loads(srv.openplz_lookup_postal_code("10115"))
        self.assertNotIn("error", out)
        self.assertEqual(out["postal_code"], "10115")
        self.assertGreaterEqual(out["count"], 1)
        self.assertEqual(out["localities"][0]["name"], "Berlin")
        print(f"\nLIVE 10115: {out['count']} locality/localities")

    def test_search_locality_live(self):
        out = json.loads(srv.openplz_search_locality("München", limit=5))
        self.assertNotIn("error", out)
        codes = [r["postal_code"] for r in out["localities"]]
        self.assertIn("80331", codes)
        munich = next(r for r in out["localities"]
                      if r["postal_code"] == "80331")
        self.assertEqual(munich["federal_state"]["name"], "Bayern")
        print(f"\nLIVE München: {out['count']} rows, 80331 present")

    def test_search_street_live(self):
        out = json.loads(srv.openplz_search_street(
            name="Ackerstr.", postal_code="10115"))
        self.assertNotIn("error", out)
        self.assertEqual(out["count"], 1)
        self.assertEqual(out["streets"][0]["borough"], "Mitte")
        print("\nLIVE Ackerstr. 10115: 1 street, borough Mitte")

    def test_search_street_no_filter_live(self):
        out = json.loads(srv.openplz_search_street())
        self.assertIn("error", out)
        self.assertIn("at least one", out["error"])

    def test_full_text_live(self):
        out = json.loads(srv.openplz_full_text_search("10115 Berlin",
                                                      limit=5))
        self.assertNotIn("error", out)
        self.assertGreaterEqual(out["count"], 1)
        self.assertTrue(all(s["postal_code"] == "10115"
                            for s in out["streets"]))
        print(f"\nLIVE full-text '10115 Berlin': {out['count']} streets")

    def test_federal_states_live(self):
        out = json.loads(srv.openplz_list_federal_states())
        self.assertNotIn("error", out)
        self.assertEqual(out["count"], 16)
        names = [s["name"] for s in out["federal_states"]]
        self.assertIn("Berlin", names)
        self.assertIn("Bayern", names)
        print("\nLIVE federal states: 16")

    def test_admin_children_live(self):
        out = json.loads(srv.openplz_admin_children(
            "federal_state", "11", "districts"))
        self.assertNotIn("error", out)
        self.assertEqual(out["count"], 1)
        self.assertEqual(out["children"][0]["key"], "11000")
        out2 = json.loads(srv.openplz_admin_children(
            "district", "16076", "localities", limit=3))
        self.assertNotIn("error", out2)
        self.assertGreaterEqual(out2["count"], 1)
        self.assertEqual(out2["children"][0]["name"], "Bethenhausen")
        self.assertEqual(out2["children"][0]["district"]["key"], "16076")
        print("\nLIVE admin: Berlin state -> 1 district; Greiz -> localities")

    def test_admin_children_bad_combo_live(self):
        out = json.loads(srv.openplz_admin_children(
            "district", "11000", "districts"))
        self.assertIn("error", out)

    def test_health_live(self):
        out = json.loads(srv.openplz_health())
        self.assertEqual(out["status"], "ok")
        self.assertEqual(out["http_status"], 200)
        print(f"\nLIVE health: {out['status']} {out['http_status']}")


if __name__ == "__main__":
    unittest.main()
