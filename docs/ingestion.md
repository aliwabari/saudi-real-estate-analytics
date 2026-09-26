# CSV ingestion with pandas

The main script is `src/ingestion/load_raw.py`. It follows five steps: find CSVs, read them, map columns, convert values, and insert rows with a printed count.

## Read the code in this order

1. **FOLDERS / MAPPINGS / COLUMNS**: source folders, header names, and SQL column order.
2. **read_file()**: returns one prepared pandas DataFrame.
3. **to_decimal()**: the small helper used for exact decimal conversion and two-place rounding.
4. **main()**: loops over files, optionally inserts the DataFrame rows, and prints counts.

Inside `read_file()`, the main pandas operations are:

| Operation | Purpose |
|---|---|
| `pd.read_csv(..., dtype=str, keep_default_na=False)` | Read text without losing reference-number leading zeros or interpreting literal text such as NA as missing |
| `df.columns.str.strip()` | Remove spaces around header names |
| `df.rename(columns=...)` | Map source names to SQL names |
| `df.replace(...).dropna(how="all")` | Mark blank cells as missing and skip completely empty records |
| `df[COLUMNS[table]]` | Select and order the original business columns |
| `pd.to_numeric(...).astype("Int64")` | Convert count/year/quarter columns, allowing missing values |
| `Series.map(to_decimal)` | Convert prices, areas, and averages using Decimal |
| `pd.to_datetime(...).dt.date` | Convert the source date format explicitly |
| `df.astype(object).where(pd.notna(df), None)` | Prepare missing values as Python None for SQL NULL |
| `df.itertuples(index=False, name=None)` | Pass ordinary row values to pyodbc, excluding the DataFrame index |

Pandas prepares the data; pyodbc sends parameterized INSERT statements. Decimal preserves the previous exact rounding rule for DECIMAL(18,2). NumPy is installed as a pandas dependency; no direct NumPy calls make this script simpler. Path remains the tool for discovering files.

## Run from the project folder

Install dependencies: `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`

Read and convert all files, without opening a database connection:

```powershell
.\.venv\Scripts\python.exe .\src\ingestion\load_raw.py
```

For a first load into empty raw tables:

```powershell
.\.venv\Scripts\python.exe .\src\ingestion\load_raw.py --load
```

Your data is already loaded. The load command stops if either raw table contains data. This is a one-time loader, not an incremental system. Each successfully inserted file is committed; a failure rolls back the current file. Earlier committed files remain, so a partial load needs review before retrying.

## Other Python files

- `preview_sales.py`: pandas reads five rows from the first sales file and displays the headers and `df.head()`.
- `discover_files.py`: Path lists all source filenames; pandas is unnecessary for this task.
- `test_connection.py`: pyodbc tests SQL connectivity; pandas is unnecessary for this task.

## Source rules and existing data

The known 2023 Q1 sales file uses month/day/year and lacks HijriDate; other sales dates use year/month/day. Text is preserved. Only the original ten sales and seven rental columns are selected; extra fields remain in the unchanged CSV files. Decimal values are rounded to two places for the existing SQL types. Invalid numbers/dates raise errors rather than silently becoming NULL.

The 2025 Q2 sales file contains April–June 2024 dates; the script preserves them. The existing 1,269,500 sales and 17,792 rental rows were not reloaded during this refactor. Previous SQL tracking columns/table and JSON values remain in the database and are not used by the simplified loader.

For a new database, run `sql/00_create_database.sql`, then `sql/raw/01_create_raw_tables.sql`. `sql/raw/DisplayRawtables.sql` shows samples and row counts. Python does not run these SQL files automatically.

Pandas references: [read_csv](https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html), [to_numeric](https://pandas.pydata.org/docs/reference/api/pandas.to_numeric.html), [to_datetime](https://pandas.pydata.org/docs/reference/api/pandas.to_datetime.html).
