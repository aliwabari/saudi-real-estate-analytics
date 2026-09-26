from pathlib import Path

import pandas as pd

project_root = Path(__file__).resolve().parents[2]
csv_path = (
    project_root / "data" / "raw"
    / "MOJ Real Estate Sales Transactions (2020–2026 Q1)"
    / "MOJ-Sales-2020-Q1.csv"
)

# نقرأ خمسة صفوف فقط للمعاينة، ونحافظ على القيم كنصوص كما وردت في المصدر.
df = pd.read_csv(csv_path, encoding="utf-8-sig", dtype=str,
                 keep_default_na=False, nrows=5)

print("Column names:")
print(df.columns.tolist())

print("\nFirst 5 rows:")
print(df.head().to_string(index=False))
