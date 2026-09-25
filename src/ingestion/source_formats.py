"""Source layouts and minimal conversions for raw ingestion; no business cleaning."""

import csv
import hashlib
import json
import re
from collections import Counter
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path


FOLDERS = {
    "MOJ_Sales": "MOJ Real Estate Sales Transactions (2020–2026 Q1)",
    "REGA_Rentals": "REGA Rental Market Indicators (2019–2024)",
}
SALES_COLUMNS = (
    "Region", "City", "Neighborhood", "TransactionReference", "GregorianDate",
    "HijriDate", "PropertyClassification", "PropertyCount", "Price", "Area",
)
RENTAL_COLUMNS = ("Year", "Quarter", "Region", "City", "PropertyType", "TotalDeals", "AverageValue")
COLUMNS = {"MOJ_Sales": SALES_COLUMNS, "REGA_Rentals": RENTAL_COLUMNS}
SALES_MAP = dict(zip(
    ("المنطقة", "المدينة", "المدينة / الحي", "الرقم المرجعي للصفقة", "تاريخ الصفقة ميلادي",
     "تاريخ الصفقة هجري", "تصنيف العقار", "عدد العقارات", "السعر", "المساحة"), SALES_COLUMNS
))
SALES_MAP.update({"الحي": "Neighborhood", "رقم مرجعي": "TransactionReference",
                  "التاريخ": "GregorianDate", "السعر بالريال السعودي": "Price"})
RENTAL_MAP = dict(zip(
    ("السنة", "الربع", "المنطقة", "المدينة", "نوع العقار", "مجموع الصفقات", "المتوسط"), RENTAL_COLUMNS
))
RENTAL_MAP.update(dict(zip(
    ("year", "quarter", "region_ar", "city_ar", "Category", "total_deals", "average"), RENTAL_COLUMNS
)))
TEXT_LENGTHS = {"Region": 100, "City": 100, "Neighborhood": 200,
                "TransactionReference": 100, "HijriDate": 20,
                "PropertyClassification": 100, "PropertyType": 150}
INTEGER_COLUMNS = {"Year", "Quarter", "PropertyCount", "TotalDeals"}
DECIMAL_COLUMNS = {"Price", "Area", "AverageValue"}
NUMBER = re.compile(r"^[+-]?(?:[0-9]+|[0-9]{1,3}(?:,[0-9]{3})+)(?:\.[0-9]+)?$")


def file_hash(path):
    with path.open("rb") as file:
        return hashlib.file_digest(file, "sha256").hexdigest()


def discover(root):
    result = []
    for target, folder in FOLDERS.items():
        directory = root / "data" / "raw" / folder
        files = sorted(directory.glob("*.csv"))
        if not files:
            raise ValueError(f"No CSV files found in {directory}")
        result.extend((target, path) for path in files)
    return result


def numeric(value):
    value = value.strip()
    if not NUMBER.fullmatch(value):
        raise ValueError(f"Unsupported numeric value: {value!r}")
    return Decimal(value.replace(",", ""))


def convert(column, value, generic_date=False):
    # Preserve text as supplied. Empty/whitespace-only cells become SQL NULL.
    if not value.strip():
        return None, False
    if column in TEXT_LENGTHS:
        if len(value.encode("utf-16-le")) // 2 > TEXT_LENGTHS[column]:
            raise ValueError(f"{column} exceeds NVARCHAR({TEXT_LENGTHS[column]})")
        return value, False
    if column in INTEGER_COLUMNS:
        number = numeric(value)
        if number != number.to_integral_value() or not -(2**31) <= number < 2**31:
            raise ValueError(f"{column} is outside SQL INT or is fractional: {value!r}")
        return int(number), False
    if column in DECIMAL_COLUMNS:
        number = numeric(value)
        rounded = number.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if abs(rounded) >= Decimal("10000000000000000"):
            raise ValueError(f"{column} exceeds DECIMAL(18,2)")
        return rounded, number != rounded
    if column == "GregorianDate":
        text = value.strip()
        if generic_date:
            # Observed 2023 Q1 layout is month/day/year (e.g. 1/31/2023).
            if not re.fullmatch(r"[0-9]{1,2}/[0-9]{1,2}/[0-9]{4}", text):
                raise ValueError(f"Expected month/day/year: {value!r}")
            month, day, year = map(int, text.split("/"))
        else:
            if not re.fullmatch(r"[0-9]{4}/[0-9]{2}/[0-9]{2}", text):
                raise ValueError(f"Expected year/month/day: {value!r}")
            year, month, day = map(int, text.split("/"))
        return date(year, month, day), False
    raise ValueError(f"Unknown target column: {column}")


def read_rows(path, target, stats):
    """Yield (CSV record number, typed values, preserved extras). Header is record 1."""
    mapping = SALES_MAP if target == "MOJ_Sales" else RENTAL_MAP
    with path.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.reader(file, strict=True)
        original_headers = next(reader, None)
        if not original_headers:
            raise ValueError("CSV is empty or missing its header")
        headers = [h.strip() for h in original_headers]
        if len(set(headers)) != len(headers) or any(not h for h in headers):
            raise ValueError("Empty or duplicate CSV headers")
        mapped = [mapping.get(h) for h in headers]
        destinations = [c for c in mapped if c]
        if len(set(destinations)) != len(destinations):
            raise ValueError("Multiple source columns map to the same destination")
        required = set(COLUMNS[target])
        generic_date = target == "MOJ_Sales" and "التاريخ" in headers
        if generic_date:
            if path.name != "MOJ-Sales-2023-Q1.csv":
                raise ValueError("Generic date format needs review for this new file")
            required.remove("HijriDate")
        if required - set(destinations):
            raise ValueError(f"Missing required columns: {sorted(required - set(destinations))}")
        stats["headers"] = original_headers
        stats["extra_columns"] = [h for h, dest in zip(headers, mapped) if dest is None]
        period = re.fullmatch(r"MOJ-Sales-([0-9]{4})-Q([1-4])\.csv", path.name)
        stats.update(source_rows=0, blank_rows=0, loaded_rows=0, rounded_cells=0,
                     date_period_mismatches=0, missing_hijri_rows=0)
        for record_number, row in enumerate(reader, start=2):
            stats["source_rows"] += 1
            if not row or not any(cell.strip() for cell in row):
                stats["blank_rows"] += 1
                continue
            if len(row) != len(headers):
                raise ValueError(f"Record {record_number}: expected {len(headers)} fields, found {len(row)}")
            values = dict.fromkeys(COLUMNS[target])
            extras = {h: v for h, v, dest in zip(original_headers, row, mapped) if dest is None}
            originals = {}
            for header, cell, dest in zip(original_headers, row, mapped):
                if dest is None:
                    continue
                try:
                    value, rounded = convert(dest, cell, generic_date)
                except (ValueError, InvalidOperation) as error:
                    raise ValueError(f"Record {record_number}, {dest}: {error}") from error
                values[dest] = value
                if rounded:
                    originals[header] = cell
                    stats["rounded_cells"] += 1
            if generic_date:
                originals[original_headers[headers.index("التاريخ")]] = row[headers.index("التاريخ")]
                stats["missing_hijri_rows"] += 1
            when = values.get("GregorianDate")
            if when and period:
                if (when.year, (when.month - 1) // 3 + 1) != tuple(map(int, period.groups())):
                    stats["date_period_mismatches"] += 1
            preserved = {}
            if extras:
                preserved["extra_columns"] = extras
            if originals:
                preserved["original_values"] = originals
            payload = json.dumps(preserved, ensure_ascii=False) if preserved else None
            stats["loaded_rows"] += 1
            yield record_number, tuple(values[c] for c in COLUMNS[target]), payload


def inspect_file(path, target):
    digest = file_hash(path)
    stats = {}
    for _ in read_rows(path, target, stats):
        pass
    if file_hash(path) != digest:
        raise ValueError("Source changed during validation")
    stats["sha256"] = digest
    return stats
