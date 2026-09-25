"""Run with: python -m unittest discover -s src/ingestion -p test_source_formats.py"""
import csv
import json
import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from source_formats import convert, inspect_file, read_rows


class ConversionTests(unittest.TestCase):
    def test_numeric_precision_and_grouping(self):
        self.assertEqual(convert("Price", "1,234.50"), (Decimal("1234.50"), False))
        self.assertEqual(convert("AverageValue", "9071.428571"), (Decimal("9071.43"), True))
        self.assertEqual(convert("Price", "-1.005"), (Decimal("-1.01"), True))
        for bad in ("12,34", "NaN", "inf", "1e4"):
            with self.assertRaises(ValueError):
                convert("Price", bad)

    def test_int_and_decimal_overflow(self):
        self.assertEqual(convert("TotalDeals", "12.0"), (12, False))
        for bad in ("12.5", "2147483648"):
            with self.assertRaises(ValueError):
                convert("TotalDeals", bad)
        with self.assertRaises(ValueError):
            convert("Price", "9999999999999999.999")

    def test_dates_and_nulls(self):
        self.assertEqual(convert("GregorianDate", "2024/02/29")[0], date(2024, 2, 29))
        self.assertEqual(convert("GregorianDate", "1/31/2023", True)[0], date(2023, 1, 31))
        with self.assertRaises(ValueError):
            convert("GregorianDate", "2023/02/29")
        self.assertEqual(convert("Price", " "), (None, False))
        self.assertEqual(convert("City", " الرياض "), (" الرياض ", False))

    def test_text_never_truncated(self):
        with self.assertRaises(ValueError):
            convert("Region", "x" * 101)
        with self.assertRaises(ValueError):
            convert("Region", "😀" * 51)


class FileTests(unittest.TestCase):
    def make_file(self, directory, name, rows):
        path = Path(directory) / name
        with path.open("w", encoding="utf-8-sig", newline="") as file:
            csv.writer(file).writerows(rows)
        return path

    def test_english_rentals_rounding_extra_fields_and_blank(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.make_file(directory, "rental.csv", [
                ["year ", "quarter", "region_ar", "city_ar", "Category", "total_deals", "average", "note"],
                ["2020", "1", "الرياض", "الرياض", "شقة", "2", "100.125", "keep this"],
                [""] * 8,
            ])
            stats = {}
            rows = list(read_rows(path, "REGA_Rentals", stats))
            self.assertEqual((stats["source_rows"], stats["blank_rows"], stats["loaded_rows"]), (2, 1, 1))
            extra = json.loads(rows[0][2])
            self.assertEqual(extra["original_values"]["average"], "100.125")
            self.assertEqual(extra["extra_columns"]["note"], "keep this")

    def test_malformed_and_missing_header_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            headers = ["year", "quarter", "region_ar", "city_ar", "Category", "total_deals", "average"]
            for rows in ([headers, ["2020", "1"]], [["year", "year"], ["2020", "2020"]], [["year"], ["2020"]]):
                path = self.make_file(directory, "bad.csv", rows)
                with self.assertRaises(ValueError):
                    inspect_file(path, "REGA_Rentals")

    def test_q1_date_layout_extra_fields_and_missing_hijri(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.make_file(directory, "MOJ-Sales-2023-Q1.csv", [
                ["رقم مرجعي", "المنطقة", "المدينة", "الحي", "المخطط", "رقم القطعة", "التاريخ", "تصنيف العقار", "نوع العقار", "عدد العقارات", "السعر بالريال السعودي", "المساحة ", "سعر المتر المربع"],
                ["0001", "الرياض", "الرياض", "حي", "plan", "plot", "1/31/2023", "سكني", "أرض", "1", "100", "10", "10"],
            ])
            stats = {}
            row = list(read_rows(path, "MOJ_Sales", stats))[0]
            self.assertEqual(row[1][3], "0001")
            self.assertEqual(row[1][4], date(2023, 1, 31))
            self.assertIsNone(row[1][5])
            self.assertEqual(json.loads(row[2])["extra_columns"]["المخطط"], "plan")
            self.assertEqual(stats["missing_hijri_rows"], 1)


if __name__ == "__main__":
    unittest.main()
