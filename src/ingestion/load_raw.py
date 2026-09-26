"""Read sales/rental CSVs. Add --load only when both raw tables are empty."""

import argparse
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import pandas as pd
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


def to_decimal(value):
    """نستخدم Decimal للأسعار والمساحات حتى نحافظ على دقة التحويل والتقريب."""
    return Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def read_file(path, table):
    """قراءة CSV وتجهيز أعمدته داخل DataFrame واحد."""
    # نقرأ القيم كنصوص حتى لا نفقد الأصفار في بداية الرقم المرجعي.
    df = pd.read_csv(path, encoding="utf-8-sig", dtype=str, keep_default_na=False)

    # إزالة المسافات حول أسماء الأعمدة، ثم تحويلها إلى أسماء SQL.
    df.columns = df.columns.str.strip()
    df = df.rename(columns=MAPPINGS[table])
    if not df.columns.is_unique:
        raise ValueError(f"{path.name}: duplicate column mapping")

    # الخلايا الفارغة تصبح قيمًا مفقودة؛ نتجاوز الصف الفارغ بالكامل فقط.
    df = df.replace(r"^\s*$", pd.NA, regex=True).dropna(how="all")

    # ملف 2023 Q1 يستخدم شهر/يوم/سنة ولا يحتوي على التاريخ الهجري.
    special_date = table == "MOJ_Sales" and path.name == "MOJ-Sales-2023-Q1.csv"
    if special_date and "HijriDate" not in df.columns:
        df["HijriDate"] = pd.NA

    # اختيار الأعمدة المطلوبة وترتيبها حسب جدول SQL؛ العمود الناقص يسبب خطأ.
    df = df[COLUMNS[table]].copy()

    # تحويل أعمدة الأعداد الصحيحة. Int64 يسمح أيضًا بالقيم المفقودة.
    for column in ("Year", "Quarter", "PropertyCount", "TotalDeals"):
        if column in df.columns:
            values = df[column].str.replace(",", "", regex=False)
            df[column] = pd.to_numeric(values, errors="raise").astype("Int64")

    # تطبيق نفس التحويل على عمود كامل بدل المرور يدويًا على كل صف.
    for column in ("Price", "Area", "AverageValue"):
        if column in df.columns:
            values = df[column].str.replace(",", "", regex=False)
            df[column] = values.map(to_decimal, na_action="ignore")

    if table == "MOJ_Sales":
        date_format = "%m/%d/%Y" if special_date else "%Y/%m/%d"
        df["GregorianDate"] = pd.to_datetime(
            df["GregorianDate"].str.strip(), format=date_format, errors="raise"
        ).dt.date

    # pyodbc يحتاج None للقيم التي ستدخل إلى SQL بوصفها NULL.
    return df.astype(object).where(pd.notna(df), None)


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
                df = read_file(path, table)
                # 4. Insert using parameters: each ? receives one column value.
                if load and not df.empty:
                    columns = ", ".join(f"[{column}]" for column in COLUMNS[table])
                    placeholders = ", ".join("?" for column in COLUMNS[table])
                    sql = f"INSERT INTO raw.[{table}] ({columns}) VALUES ({placeholders})"
                    # تحويل صفوف DataFrame إلى قيم يرسلها pyodbc إلى SQL.
                    rows = list(df.itertuples(index=False, name=None))
                    cursor.executemany(sql, rows)
                    connection.commit()  # Save this file only after every row succeeds.
                # 5. Report the count for each file and the whole table.
                action = "Inserted" if load else "Read"
                print(f"{action} {len(df):,} rows: {path.name}", flush=True)
                total += len(df)
            print(f"{table}: {len(files)} files, {total:,} rows\n")
    finally:
        if connection is not None:
            connection.rollback()  # Undo the current file if it failed before commit.
            connection.close()


if __name__ == "__main__":
    main()
