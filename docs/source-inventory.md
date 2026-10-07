# Source inventory

This document summarizes the source files used in the completed project and the structural differences identified during ingestion and profiling.

## Sources

| Dataset | Local CSV files | Raw rows loaded | Analytical grain |
|---|---:|---:|---|
| MOJ real estate sales | 23 | 1,269,500 | One sale transaction |
| REGA rental indicators | 12 | 17,792 | Year + Quarter + City + Property Type |

Raw datasets are kept locally and excluded from Git.

## MOJ sales

Files follow the pattern `MOJ-Sales-YYYY-QN.csv`.

| Year | Quarters present by filename |
|---|---|
| 2020 | Q1, Q2, Q3 |
| 2021 | Q2, Q3, Q4 |
| 2022 | Q1, Q2, Q3, Q4 |
| 2023 | Q1, Q2, Q3, Q4 |
| 2024 | Q1, Q2, Q3, Q4 |
| 2025 | Q1, Q2, Q3, Q4 |
| 2026 | Q1 |

Important structural differences:

- most files use the expected ten-column Arabic layout;
- 2023 Q2 and Q3 include an additional property-type field;
- 2023 Q1 has a different layout, uses a generic date field, and has no separate Hijri date;
- the 2025 Q2 file contains Gregorian dates in April–June 2024, so the source dates were preserved rather than replaced using the filename.

## REGA rentals

The rental files contain year, quarter, region, city, property type, total deals, and average value.

Important structural differences:

- Eastern Province and Madinah use English headers;
- other files primarily use Arabic headers;
- some source headers contain trailing spaces;
- the final uniqueness grain is **Year + Quarter + City + Property Type**.

## Modeling consequence

The sources do not represent the same business event:

- MOJ sales are transaction-level records.
- REGA rentals are aggregated market indicators.

They therefore remain separate fact tables and share geography dimensions where appropriate.
