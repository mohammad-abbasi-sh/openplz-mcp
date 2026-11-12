"""Offline tests — domain logic against recorded OpenPLZ fixtures.

Run:  pytest tests/test_domain.py -v
"""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from openplz_mcp import domain as dom  # noqa: E402

FIX = pathlib.Path(__file__).resolve().parent / "fixtures"


def _read(name: str) -> str:
    return (FIX / name).read_text(encoding="utf-8")


class TestValidation(unittest.TestCase):
    def test_postal_code_ok(self):
        self.assertEqual(dom.validate_postal_code("10115"), "10115")
        self.assertEqual(dom.validate_postal_code(" 80331 "), "80331")

    def test_postal_code_bad(self):
        for bad in ("", "1011", "101155", "ABCDE", "10 115", "1011a"):
            with self.assertRaises(ValueError, msg=bad):
                dom.validate_postal_code(bad)

    def test_limit_ok(self):
        self.assertEqual(dom.validate_limit(1), 1)
        self.assertEqual(dom.validate_limit(50), 50)
        self.assertEqual(dom.validate_limit("20"), 20)

    def test_limit_bad(self):
        for bad in (0, 51, -1, "many", None):
            with self.assertRaises(ValueError, msg=str(bad)):
                dom.validate_limit(bad)


class TestUrls(unittest.TestCase):
    def test_localities_url(self):
        self.assertEqual(
            dom.localities_url(postal_code="10115", limit=50),
            "https://openplzapi.org/de/Localities?pageSize=50&postalCode=10115")
        self.assertEqual(
            dom.localities_url(name="München", limit=3),
            "https://openplzapi.org/de/Localities?pageSize=3&name=M%C3%BCnchen")

    def test_streets_url(self):
        self.assertEqual(
            dom.streets_url(name="Ackerstr.", postal_code="10115"),
            "https://openplzapi.org/de/Streets?pageSize=20&name=Ackerstr."
            "&postalCode=10115")
        self.assertEqual(
            dom.streets_url(postal_code="10115", limit=3),
            "https://openplzapi.org/de/Streets?pageSize=3&postalCode=10115")

    def test_streets_url_needs_filter(self):
        with self.assertRaises(ValueError):
            dom.streets_url()

    def test_full_text_url(self):
        self.assertEqual(
            dom.full_text_url("10115 Berlin", limit=5),
            "https://openplzapi.org/de/FullTextSearch?searchTerm=10115+Berlin"
            "&pageSize=5")
        with self.assertRaises(ValueError):
            dom.full_text_url("   ")

    def test_federal_states_url(self):
        self.assertEqual(dom.federal_states_url(),
                         "https://openplzapi.org/de/FederalStates")

    def test_admin_children_url(self):
        self.assertEqual(
            dom.admin_children_url("federal_state", "11", "districts"),
            "https://openplzapi.org/de/FederalStates/11/Districts?pageSize=20")
        self.assertEqual(
            dom.admin_children_url("district", "11000", "localities", limit=3),
            "https://openplzapi.org/de/Districts/11000/Localities?pageSize=3")
        self.assertEqual(
            dom.admin_children_url("government_region", "091", "districts"),
            "https://openplzapi.org/de/GovernmentRegions/091/Districts?pageSize=20")

    def test_admin_children_url_bad_combo(self):
        with self.assertRaises(ValueError) as cm:
            dom.admin_children_url("district", "11000", "districts")
        self.assertIn("federal_state -> districts", str(cm.exception))
        with self.assertRaises(ValueError):
            dom.admin_children_url("federal_state", "", "districts")
        with self.assertRaises(ValueError):
            dom.admin_children_url("city", "11", "districts")


class TestParsing(unittest.TestCase):
    def test_parse_localities_10115(self):
        rows = dom.parse_localities(_read("localities-10115.json"))
        self.assertEqual(len(rows), 1)
        r = rows[0]
        self.assertEqual(r["postal_code"], "10115")
        self.assertEqual(r["name"], "Berlin")
        self.assertEqual(r["municipality"]["key"], "11000000")
        self.assertEqual(r["municipality"]["name"], "Berlin, Stadt")
        self.assertEqual(r["federal_state"]["key"], "11")
        self.assertEqual(r["federal_state"]["name"], "Berlin")

    def test_parse_localities_muenchen(self):
        rows = dom.parse_localities(_read("localities-muenchen.json"))
        self.assertEqual(len(rows), 3)
        munich = next(r for r in rows if r["postal_code"] == "80331")
        self.assertEqual(munich["name"], "München")
        self.assertEqual(munich["federal_state"]["key"], "09")
        self.assertEqual(munich["federal_state"]["name"], "Bayern")
        self.assertEqual(munich["municipality"]["key"], "09162000")

    def test_parse_federal_states(self):
        rows = dom.parse_federal_states(_read("federal-states.json"))
        self.assertEqual(len(rows), 16)
        self.assertEqual([r["key"] for r in rows],
                         [f"{i:02d}" for i in range(1, 17)])
        berlin = next(r for r in rows if r["key"] == "11")
        self.assertEqual(berlin["name"], "Berlin")
        self.assertEqual(berlin["seat_of_government"], "Berlin")
        bayern = next(r for r in rows if r["key"] == "09")
        self.assertEqual(bayern["seat_of_government"], "München")

    def test_parse_streets_ackerstr(self):
        rows = dom.parse_streets(_read("streets-ackerstr-10115.json"))
        self.assertEqual(len(rows), 1)
        r = rows[0]
        self.assertEqual(r["name"], "Ackerstr.")
        self.assertEqual(r["postal_code"], "10115")
        self.assertEqual(r["locality"], "Berlin")
        self.assertEqual(r["borough"], "Mitte")
        self.assertEqual(r["suburb"], "Mitte")

    def test_parse_fulltext(self):
        rows = dom.parse_streets(_read("fulltext-10115-berlin.json"))
        self.assertEqual(len(rows), 5)
        self.assertTrue(all(r["postal_code"] == "10115" for r in rows))
        self.assertTrue(all(r["locality"] == "Berlin" for r in rows))
        self.assertEqual(rows[0]["name"], "Ackerstr.")

    def test_parse_districts_berlin(self):
        rows = dom.parse_admin_children(_read("districts-berlin.json"))
        self.assertEqual(len(rows), 1)
        r = rows[0]
        self.assertEqual(r["key"], "11000")
        self.assertEqual(r["name"], "Berlin, Stadt")
        self.assertEqual(r["type"], "Kreisfreie Stadt")
        self.assertEqual(r["federal_state"]["key"], "11")

    def test_parse_municipalities_bayern(self):
        rows = dom.parse_admin_children(_read("municipalities-bayern.json"))
        self.assertEqual(len(rows), 3)
        ingolstadt = rows[0]
        self.assertEqual(ingolstadt["key"], "09161000")
        self.assertEqual(ingolstadt["name"], "Ingolstadt")
        self.assertEqual(ingolstadt["postal_code"], "85047")
        self.assertTrue(ingolstadt["multiple_postal_codes"])
        self.assertEqual(ingolstadt["federal_state"]["key"], "09")

    def test_parse_government_regions_bayern(self):
        rows = dom.parse_admin_children(
            _read("government-regions-bayern.json"))
        self.assertEqual(len(rows), 7)
        self.assertEqual(rows[0]["key"], "091")
        self.assertEqual(rows[0]["name"], "Oberbayern")
        self.assertEqual(rows[0]["administrative_headquarters"], "München")

    def test_parse_localities_berlin_state(self):
        rows = dom.parse_localities(_read("localities-berlin-state.json"))
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(r["federal_state"]["key"] == "11" for r in rows))

    def test_parse_bad_json(self):
        with self.assertRaises(ValueError):
            dom.parse_localities("not json {")
        with self.assertRaises(ValueError):
            dom.parse_localities('{"not": "a list"}')
        with self.assertRaises(ValueError):
            dom.parse_federal_states("[] trailing")


if __name__ == "__main__":
    unittest.main()
