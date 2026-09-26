# Saudi Real Estate Analytics

A Peak portfolio project to build an end-to-end analysis of Saudi real estate sales and rentals using SQL Server, Python, Power BI, and GitHub.

## Current status

Raw ingestion is implemented. All 23 MOJ sales files (1,269,500 rows) and 12 REGA rental files (17,792 rows) were loaded locally into SQL Server by the earlier loader. The current ingestion script is a simpler, one-file implementation for reading CSVs, mapping columns, converting values, inserting rows, and printing counts. It stops if either destination table already contains data. Core normalization, analysis, and dashboards remain future steps. See [the ingestion guide](docs/ingestion.md) for commands, conversion rules, and known data issues.

## Planned data flow

CSV files → Python ingestion → SQL Server raw schema → SQL cleaning and normalization → core relational model → analytical/star model → Power BI.

Python discovers source files, maps their columns, converts dates and numbers, inserts rows into raw tables, and prints row counts. Heavy analytical cleaning belongs after raw ingestion.

## Sources and grain

| Source | Grain | Local files |
|---|---|---:|
| MOJ real estate sales | One individual sale transaction | 23 |
| REGA rental indicators | Year + Quarter + Region + City + PropertyType | 12 |
| MOJ historical real estate indices | To be examined separately | 3 |

Sales and rentals have different grains and will not share one fact table. TransactionReference is not assumed to be a primary key; uniqueness must be tested.

Raw datasets are kept locally and excluded from Git. Cloning this repository will not download them. Existing source files must not be renamed, moved, overwritten, or deleted without approval.

## Database decisions

Database: `SaudiRealEstateAnalytics`.

- `raw`: source/staging representation imported from CSV files.
- `core`: normalized relational model.

Confirmed geography design:

- Region: RegionID (PK), RegionName.
- City: CityID (PK), CityName, RegionID (FK).
- Neighborhood: NeighborhoodID (PK), NeighborhoodName, CityID (FK).

Region has many cities; each city belongs to one region. City has many neighborhoods; each neighborhood belongs to one city. The remainder of the ERD is not finalized.

## Project structure

```text
data/raw/              Existing local datasets; excluded from Git
src/ingestion/         Simple loader and learning scripts
src/transformation/    Reserved for later Python transformations if needed
sql/raw/               Staging definitions, ingestion metadata, and checks
sql/core/              Future agreed relational model and normalization
notebooks/             Future exploration and profiling
powerbi/               Future Power BI report/project files
docs/                  Source inventory and technical decisions
requirements.txt       Pinned Python dependency for SQL Server access
```

Empty development folders use `.gitkeep` placeholders because Git tracks files rather than empty directories. Python uses a local `.venv` and the dependency declared in `requirements.txt`; environments, raw datasets, and ingestion logs are excluded from Git.

See [the source inventory](docs/source-inventory.md) for observed coverage and header differences. Work proceeds one major step at a time, with database designs proposed and reviewed before implementation.