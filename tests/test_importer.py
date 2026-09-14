import csv
import sqlite3
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tcc_sales.dataset import DataValidationError
from tcc_sales.importer import connect, import_folder


class ImporterTests(unittest.TestCase):
    def test_real_demo_import_is_idempotent_and_tenant_scoped(self):
        with tempfile.TemporaryDirectory() as directory:
            with closing(connect(Path(directory) / "test.sqlite3")) as connection:
                first = import_folder(connection, ROOT / "data/raw/maven", "tenant-a")
                repeated = import_folder(connection, ROOT / "data/raw/maven", "tenant-a")
                second_tenant = import_folder(connection, ROOT / "data/raw/maven", "tenant-b")
                counts = dict(connection.execute("SELECT tenant_id, COUNT(*) FROM opportunities GROUP BY tenant_id"))
                aliases = connection.execute(
                    "SELECT COUNT(*) FROM opportunities WHERE tenant_id='tenant-a' AND source_product='GTXPro' AND product='GTX Pro'"
                ).fetchone()[0]
            self.assertEqual(first["status"], "imported")
            self.assertEqual(repeated["status"], "skipped")
            self.assertEqual(second_tenant["status"], "imported")
            self.assertEqual(counts, {"tenant-a": 8800, "tenant-b": 8800})
            self.assertEqual(aliases, 1480)

    def test_invalid_date_reports_row_and_field_without_partial_import(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory) / "source"
            folder.mkdir()
            files = {
                "accounts.csv": [["account", "sector", "year_established", "revenue", "employees", "office_location", "subsidiary_of"], ["A", "Tech", "2000", "10", "5", "SP", ""]],
                "products.csv": [["product", "series", "sales_price"], ["P", "S", "100"]],
                "sales_teams.csv": [["sales_agent", "manager", "regional_office"], ["V", "G", "SP"]],
                "sales_pipeline.csv": [["opportunity_id", "sales_agent", "product", "account", "deal_stage", "engage_date", "close_date", "close_value"], ["1", "V", "P", "A", "Won", "31/01/2026", "2026-02-01", "100"]],
            }
            for filename, rows in files.items():
                with (folder / filename).open("w", encoding="utf-8", newline="") as handle:
                    csv.writer(handle).writerows(rows)
            database = Path(directory) / "test.sqlite3"
            with closing(connect(database)) as connection:
                with self.assertRaises(DataValidationError) as caught:
                    import_folder(connection, folder)
                tenant_count = connection.execute("SELECT COUNT(*) FROM tenants").fetchone()[0]
            self.assertIn("linha 2, campo engage_date", str(caught.exception))
            self.assertEqual(tenant_count, 0)


if __name__ == "__main__":
    unittest.main()
