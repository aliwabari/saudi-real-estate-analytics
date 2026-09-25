# Source inventory

Inspected on 2026-09-25. Inventory and first-line header inspection only; row counts, value types, actual date coverage, and key uniqueness have not been validated.

## Existing folders

| Folder under data/raw | CSV files | Bytes |
|---|---:|---:|
| MOJ Real Estate Sales Transactions (2020–2026 Q1) | 23 | 169,379,863 |
| REGA Rental Market Indicators (2019–2024) | 12 | 1,304,409 |
| MOJ Historical Real Estate Indices (2018–2021) | 3 | 264,150 |

## Sales

Files follow `MOJ-Sales-YYYY-QN.csv`.

| Year | Quarters present by filename |
|---|---|
| 2020 | Q1, Q2, Q3 |
| 2021 | Q2, Q3, Q4 |
| 2022 | Q1, Q2, Q3, Q4 |
| 2023 | Q1, Q2, Q3, Q4 |
| 2024 | Q1, Q2, Q3, Q4 |
| 2025 | Q1, Q2, Q3, Q4 |
| 2026 | Q1 |

2020 Q4 and 2021 Q1 are absent by filename. Their transaction coverage has not been checked.

Twenty files share the expected ten-column Arabic header. 2023 Q2 and Q3 add property type. 2023 Q1 has 13 columns, including plan, plot number, property type, price per square metre, and a generic date column instead of separately labeled Gregorian and Hijri dates.

Before ingestion, agree how to preserve extra source fields and interpret the 2023 Q1 date. No raw-table implementation has been created.

## Rentals

Regional filenames identify Al-Baha, Al-jawf, Eastern-Province, Hail, Jazan, Madinah, Makkah, N-B, Najran, Qassim, Riyadh, and Tabuk. No Asir-named file was found.

Eastern-Province and Madinah use English headers: `year,quarter,region_ar,city_ar,Category,total_deals,average`. Other files use Arabic headers; Al-Baha, Makkah, and Riyadh include trailing spaces in some headers.

## Historical indices

- `MOJ-RE-Index-Cities-2018-2021.csv`
- `MOJ-RE-Index-Districts-2018-2021.csv`
- `MOJ-RE-Index-Regions-2018-2021.csv`

Headers contain title text, Unnamed columns, or repeated years. These files require separate structural inspection. Their target tables and ingestion approach are not yet agreed.