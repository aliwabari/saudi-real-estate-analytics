# CSV ingestion into SQL Server

## Scope

Load every CSV in the existing MOJ sales and REGA rental folders into their respective `raw` tables. Historical indices, core normalization, and analytical modeling are outside this ingestion step. Original CSV files are read only.

The entry point is `src/ingestion/load_raw.py`. `source_formats.py` contains column mappings and conversions. The earlier learning scripts are retained.

## Run from the project folder

Validate every source file without connecting to SQL Server:

```powershell
.\.venv\Scripts\python.exe .\src\ingestion\load_raw.py
```

Validate and load files that have not already been loaded:

```powershell
.\.venv\Scripts\python.exe .\src\ingestion\load_raw.py --load
```

Run conversion tests:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s src/ingestion -p test_source_formats.py -v
```

If setting up Python again, use Python 3.14, create `.venv` with `python -m venv .venv`, and install the declared dependency with `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`.

The default connection uses Windows Authentication, the local SQL Server, and `SaudiRealEstateAnalytics`. It uses ODBC Driver 18, encrypted transport, and trusts the local development server certificate. For a remote server, provide an appropriate connection string through the `PEAK_SQL_CONNECTION_STRING` environment variable, including certificate validation. Connection strings are not logged; keep credentials out of code and Git. No `.env` file is read automatically.

For a new database, run `sql/00_create_database_and_raw_schema.sql` and then `sql/raw/01_create_raw_tables.sql` in SSMS. The loader applies `02_ingestion_tracking.sql` itself. Your existing database and raw tables were already present and were retained. `03_validate_ingestion.sql` contains read-only checks for SSMS.

## What happens during a run

1. Discover the two explicitly named source folders. An absent or empty folder is an error.
2. Validate every CSV before making database changes: header mapping, field counts, text lengths, numeric ranges, dates, and row counts.
3. Acquire a SQL application lock so two instances of this loader cannot run simultaneously.
4. Check the existing business-column definitions and add ingestion metadata if missing.
5. Check the file ledger against database row counts. Untracked existing rows stop the load for review.
6. Skip successfully loaded content. Reject a changed file at a previously loaded path.
7. Insert each new file in batches, checking counts and its SHA-256 before committing that file.

Each file is one SQL transaction. A failed file leaves no committed rows or successful ledger entry; earlier successfully committed files remain. A restart skips those earlier files and resumes. The loader does not delete or replace existing rows.

## Structural conversion rules

| Source feature | Ingestion behavior |
|---|---|
| Arabic and English headers, trailing header spaces | Map explicitly to the agreed SQL column names |
| Text values | Preserve spelling, leading zeros, and nonempty whitespace as supplied |
| Empty or whitespace-only cell | SQL NULL |
| Entirely blank CSV record | Skip and count it in the file ledger |
| Prices/areas such as `1,234.50` | Validate grouping and parse with Python Decimal |
| SQL INT columns | Require an exact integer within SQL INT range |
| Values beyond two decimal places | Round half away from zero to fit the existing DECIMAL(18,2); retain the exact original string in SourceExtraJson |
| Standard MOJ date | Parse explicit year/month/day |
| 2023 Q1 generic date | Parse month/day/year, confirmed by values such as `1/31/2023`; preserve the original string |
| 2023 Q1 missing Hijri date | NULL; no invented date conversion |
| Extra source fields | Preserve them in SourceExtraJson |
| Invalid number/date, overlong text, missing header, malformed row | Fail validation; do not silently truncate or replace bad values with NULL |
| Date inconsistent with filename | Count a warning; preserve the supplied date |

No deduplication by TransactionReference, geography cleaning, neighborhood splitting, classification harmonization, or outlier filtering occurs. TransactionReference has no new uniqueness constraint. Duplicate business rows across different source files remain available for later SQL quality checks.

## SQL tracking additions

`sql/raw/02_ingestion_tracking.sql` adds three columns to each existing raw table without changing its business columns:

- `IngestionFileID`: links the row to its source-file ledger entry.
- `SourceRowNumber`: logical CSV record number, with the header counted as record 1. This is not necessarily the physical line number if a quoted field contains newlines.
- `SourceExtraJson`: extra source fields and original values requiring precision reduction or generic-date interpretation.

`raw.IngestionFiles` records the relative source path, SHA-256, file size, headers, counts, loader version, and UTC load time. Each entry represents one successfully committed file. The unique source-file/record index protects ingestion identity; it is not a business key or a finalized core ERD decision.

Full CSV bytes remain in the original source files. SourceExtraJson preserves otherwise unrepresented values but is not a copy of every original row. It can be read using SQL Server JSON functions.

Each run writes a timestamped `.log` and `.json` report under `logs/`, which is excluded from Git. Reports show validation failures, skipped files, successful loads, counts, and warnings. An interrupted process may not write its final report, but its uncommitted SQL transaction rolls back and the SQL ledger remains authoritative.

## Known source issues

- `MOJ-Sales-2025-Q2.csv`: all 47,518 records have dates inconsistent with its filename. Do not treat filename coverage as verified transaction coverage.
- Twelve completely blank sales records are counted and skipped.
- Some sales values and many rental averages need more precision than DECIMAL(18,2). The originals are retained in SourceExtraJson for a later schema/analysis decision.
- 2020 Q4 and 2021 Q1 are absent by sales filename; no Asir-named rental file is present.

The loader does not infer corrections for these issues.

## Recovery and limits

For a failed run, read the newest report, resolve its specific issue, and rerun. Previously loaded files are skipped. If a source file has changed since loading, or database row counts no longer match the ledger, stop for an explicit reload/reconciliation decision. Do not clear the ledger alone.

The application lock coordinates this loader only; it does not stop unrelated manual SQL edits. Reconciliation detects row-count differences, not arbitrary edits that leave counts unchanged. Schema additions require suitable database permissions on the first load.

References: [pyodbc parameter types and sizes](https://github.com/mkleehammer/pyodbc/blob/master/src/pyodbc.pyi), [SQL Server application locks](https://learn.microsoft.com/en-us/sql/relational-databases/system-stored-procedures/sp-getapplock-transact-sql).
