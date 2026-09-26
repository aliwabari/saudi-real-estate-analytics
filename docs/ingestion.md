# Simple CSV ingestion

Everything is in `src/ingestion/load_raw.py`. Read it from top to bottom:

1. **FOLDERS** names the two CSV folders.
2. **SALES_MAP / RENTAL_MAP** connect source headers to SQL column names.
3. **convert_value()** converts strings into integers, decimals, dates, or NULL.
4. **read_file()** reads one CSV and puts its values in SQL column order.
5. **main()** loops over the files, inserts rows, and prints counts.

## Run it

From the project folder, read and convert all CSVs without connecting to SQL Server:

```powershell
.\.venv\Scripts\python.exe .\src\ingestion\load_raw.py
```

For a first load into **empty** raw tables:

```powershell
.\.venv\Scripts\python.exe .\src\ingestion\load_raw.py --load
```

Your data is already loaded. The second command will stop before inserting anything because the tables contain data. This script does not clear tables or automatically resume a partial load. If a file fails after earlier files committed, review that partial load before trying again.

## The few source-specific rules

- Headers have surrounding spaces removed; Arabic and English rental headers are supported.
- Numbers such as `1,234.50` become Decimal values. SQL DECIMAL(18,2) requires rounding to two places; the original precision remains in the CSV.
- Standard sales dates use year/month/day. The known 2023 Q1 file uses month/day/year and has no HijriDate, so that column receives NULL.
- Empty cells become NULL. Completely empty records are skipped.
- Text stays as supplied. Dates are not changed to match filenames: the 2025 Q2 sales file actually contains April–June 2024 dates.
- Only the original ten sales columns and seven rental columns are inserted. Extra CSV columns remain in the unchanged source files; the simplified loader does not copy them to SQL JSON.

The connection uses Windows Authentication to the local SQL Server. `?` placeholders pass values separately from SQL text. `executemany()` inserts the rows from one file; `commit()` saves them. If insertion fails, `rollback()` undoes the current file. Reading one file at a time keeps the code straightforward; ordinary executemany is slower than the previous optimized loader.

## Existing database and earlier code

The completed load of 1,269,500 sales rows and 17,792 rental rows is unchanged. Existing tracking columns, file ledger, and preserved JSON values remain in SQL Server. This simplified script does not use or maintain them.

For a new SQL Server setup, run `sql/00_create_database.sql`, then `sql/raw/01_create_raw_tables.sql`. These create the database, raw/core schemas, and the two raw tables only when missing. Your database is already set up. Use `sql/raw/DisplayRawtables.sql` to view small samples and row counts. Python does not execute these SQL files automatically. The previous tracking scripts are available in Git history; `docs/ingestion-validation.md` records the earlier completed load.
