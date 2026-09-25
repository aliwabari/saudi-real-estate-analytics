# Ingestion validation — 2026-09-25

| Destination | Files loaded | Source records | Blank records skipped | Rows committed |
|---|---:|---:|---:|---:|
| raw.MOJ_Sales | 23 | 1,269,512 | 12 | 1,269,500 |
| raw.REGA_Rentals | 12 | 17,792 | 0 | 17,792 |
| Total | 35 | 1,287,304 | 12 | 1,287,292 |

## Checks completed

- Seven automated tests passed for numeric grouping, precision, integer/decimal overflow, dates, nulls, Unicode length, malformed headers/rows, English rentals, source-field preservation, and the 2023 Q1 sales layout.
- Full source-to-database comparison passed for every committed row: all mapped fields, source record numbers, and preserved JSON values matched the loader's source conversions.
- SHA-256 checks confirmed all 35 loaded CSVs matched their recorded source contents.
- A deliberate row-count mismatch rolled back the entire test file and its ledger entry.
- A second simultaneous loader was rejected by the SQL application lock.
- Changed content at an already loaded path was rejected.
- Identical file content under a different path was detected by its hash.
- A second full ingestion run skipped all 35 files. Database row counts remained 1,269,500 and 17,792.

## Source facts requiring later review

- All 47,518 dates in `MOJ-Sales-2025-Q2.csv` fall between 2024-04-01 and 2024-06-30. Those dates were preserved.
- 277 sales numeric cells and 11,372 rental-average cells required rounding to fit the existing DECIMAL(18,2) columns. Exact original strings were retained in SourceExtraJson.
- The 44,091 rows in 2023 Q1 lack a separate Hijri date column; HijriDate was loaded as NULL. Extra fields and the original month/day/year date strings were retained.

These checks establish ingestion completeness and fidelity to the documented mappings. They do not establish transaction-reference uniqueness, eliminate source duplicates, validate geography, or prove business accuracy. Those checks belong to the later SQL cleaning and modeling work.

## Performance adjustment

An initial parallel reconciliation query stalled during verification. The loader's reconciliation queries were changed to use a single worker and an explicit non-null file-ID predicate for the filtered tracking index. The subsequent complete verification and repeat ingestion run succeeded. Query-level settings are contained in the scripts.

Machine-local run reports are under `logs/`; raw datasets, environments, and logs are excluded from Git.
