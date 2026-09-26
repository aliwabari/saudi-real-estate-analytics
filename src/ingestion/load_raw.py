"""Read sales/rental CSVs. Add --load only when both raw tables are empty."""

import argparse
import csv
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import pyodbc

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_FOLDER = PROJECT_ROOT / "data" / "raw"

# 1. Find the CSV files in these two folders.
FOLDERS = {
    "MOJ_Sales": "MOJ Real Estate Sales Transactions (2020–2026 Q1)",
    "REGA_Rentals": "REGA Rental Market Indicators (2019–2024)",
}

# 2. Map each source header to its SQL column name.
SALES_MAP = {
    "المنطقة": "Region", "المدينة": "City",
    "المدينة / الحي": "Neighborhood", "الحي": "Neighborhood",
    "الرقم المرجعي للصفقة": "TransactionReference", "رقم مرجعي": "TransactionReference",
    "تاريخ الصفقة ميلادي": "GregorianDate", "التاريخ": "GregorianDate",
    "تاريخ الصفقة هجري": "HijriDate", "تصنيف العقار": "PropertyClassification",
    "عدد العقارات": "PropertyCount", "السعر": "Price",
    "السعر بالريال السعودي": "Price", "المساحة": "Area",
}
RENTAL_MAP = {
    "السنة": "Year", "year": "Year",
    "الربع": "Quarter", "quarter": "Quarter",
    "المنطقة": "Region", "region_ar": "Region",
    "المدينة": "City", "city_ar": "City",
    "نوع العقار": "PropertyType", "Category": "PropertyType",
    "مجموع الصفقات": "TotalDeals", "total_deals": "TotalDeals",
    "المتوسط": "AverageValue", "average": "AverageValue",
}
MAPPINGS = {"MOJ_Sales": SALES_MAP, "REGA_Rentals": RENTAL_MAP}
COLUMNS = {
    "MOJ_Sales": ["Region", "City", "Neighborhood", "TransactionReference",
                  "GregorianDate", "HijriDate", "PropertyClassification",
                  "PropertyCount", "Price", "Area"],
    "REGA_Rentals": ["Year", "Quarter", "Region", "City", "PropertyType",
                     "TotalDeals", "AverageValue"],
}


def convert_value(column, value, date_format):
    """3. Convert CSV strings into the types expected by SQL Server."""
    if not value.strip():
        return None
    if column in ("Year", "Quarter", "PropertyCount", "TotalDeals"):
        number = Decimal(value.replace(",", ""))
        if number != number.to_integral_value():
            raise ValueError(f"{column} must be a whole number: {value}")
        return int(number)
    if column in ("Price", "Area", "AverageValue"):
        number = Decimal(value.replace(",", ""))
        return number.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if column == "GregorianDate":
        return datetime.strptime(value.strip(), date_format).date()
    return value  # Keep text, including transaction-reference leading zeros.


def read_file(path, table):
    """Read one file and return rows in the same order as the SQL columns."""
    rows = []
    with path.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file, strict=True)
        if not reader.fieldnames:
            raise ValueError(f"{path.name}: missing headers")
        reader.fieldnames = [header.strip() for header in reader.fieldnames]
        mapping = MAPPINGS[table]
        mapped_headers = [mapping[h] for h in reader.fieldnames if h in mapping]
        if len(reader.fieldnames) != len(set(reader.fieldnames)) or len(mapped_headers) != len(set(mapped_headers)):
            raise ValueError(f"{path.name}: duplicate column mapping")
        # Only the known 2023 Q1 layout lacks HijriDate and uses month/day/year.
        special_date = table == "MOJ_Sales" and path.name == "MOJ-Sales-2023-Q1.csv"
        date_format = "%m/%d/%Y" if special_date else "%Y/%m/%d"
        required = set(COLUMNS[table]) - ({"HijriDate"} if special_date else set())
        if not required.issubset(mapped_headers):
            raise ValueError(f"{path.name}: missing expected columns")
        for record_number, source_row in enumerate(reader, start=2):
            try:
                if None in source_row or None in source_row.values():
                    raise ValueError("row has the wrong number of fields")
                if not any(value.strip() for value in source_row.values()):
                    continue  # Ignore completely empty records.
                row = dict.fromkeys(COLUMNS[table])
                for header, value in source_row.items():
                    if header in mapping:
                        column = mapping[header]
                        row[column] = convert_value(column, value, date_format)
                rows.append(tuple(row[column] for column in COLUMNS[table]))
            except (ValueError, ArithmeticError) as error:
                raise ValueError(f"{path.name}, record {record_number}: {error}") from error
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--load", action="store_true", help="Insert into empty SQL raw tables")
    load = parser.parse_args().load
    connection = None
    try:
        if load:
            connection = pyodbc.connect(
                "DRIVER={ODBC Driver 18 for SQL Server};SERVER=localhost;"
                "DATABASE=SaudiRealEstateAnalytics;Trusted_Connection=yes;"
                "Encrypt=yes;TrustServerCertificate=yes;",  # Local development server.
                timeout=10,
            )
            connection.timeout = 60
            cursor = connection.cursor()
            # This is a one-time loader, not an incremental loading system.
            for table in FOLDERS:
                if cursor.execute(f"SELECT TOP (1) 1 FROM raw.[{table}]").fetchone():
                    print(f"raw.{table} already contains data. Nothing was inserted.")
                    return

        for table, folder in FOLDERS.items():
            files = sorted((RAW_FOLDER / folder).glob("*.csv"))
            if not files:
                raise ValueError(f"No CSV files found in {folder}")
            total = 0
            for path in files:
                rows = read_file(path, table)
                # 4. Insert using parameters: each ? receives one column value.
                if load and rows:
                    columns = ", ".join(f"[{column}]" for column in COLUMNS[table])
                    placeholders = ", ".join("?" for column in COLUMNS[table])
                    sql = f"INSERT INTO raw.[{table}] ({columns}) VALUES ({placeholders})"
                    cursor.executemany(sql, rows)
                    connection.commit()  # Save this file only after every row succeeds.
                # 5. Report the count for each file and the whole table.
                action = "Inserted" if load else "Read"
                print(f"{action} {len(rows):,} rows: {path.name}", flush=True)
                total += len(rows)
            print(f"{table}: {len(files)} files, {total:,} rows\n")
    finally:
        if connection is not None:
            connection.rollback()  # Undo the current file if it failed before commit.
            connection.close()


if __name__ == "__main__":
    main()
