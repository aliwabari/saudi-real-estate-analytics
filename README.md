# Saudi Real Estate Analytics

A Peak portfolio project to build an end-to-end analysis of Saudi real estate sales and rentals using SQL Server, Python, Power BI, and GitHub.

## Current status

Project structure and initial documentation only. Ingestion, database implementation, analysis, and dashboards have not been built yet.

## Planned data flow

CSV files → Python ingestion → SQL Server raw schema → SQL cleaning and normalization → core relational model → analytical/star model → Power BI.

Python will discover source files, standardize column names, handle structural differences, load raw tables, log loaded files, and validate row counts and errors. Heavy analytical cleaning belongs after raw ingestion.

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
src/ingestion/         Future file discovery, mapping, loading, validation
src/transformation/    Reserved for later Python transformations if needed
sql/raw/               Future staging definitions and checks
sql/core/              Future agreed relational model and normalization
notebooks/             Future exploration and profiling
powerbi/               Future Power BI report/project files
docs/                  Source inventory and technical decisions
requirements.txt       Dependencies added as implementation is agreed
```

Empty development folders use `.gitkeep` placeholders because Git tracks files rather than empty directories. No Python dependencies have been selected yet.

See [the source inventory](docs/source-inventory.md) for observed coverage and header differences. Work proceeds one major step at a time, with database designs proposed and reviewed before implementation.