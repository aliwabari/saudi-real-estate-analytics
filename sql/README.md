# SQL layer

SQL Server is split into three logical layers:

- **raw** — source-shaped ingestion tables;
- **core** — normalized relational tables with keys and constraints;
- **analytics** — reporting views used by Power BI.

Recommended reading order:

1. `00_create_database.sql`
2. `raw/01_create_raw_tables.sql`
3. `profiling/01_profile_raw_data.sql`
4. `core/02_create_core_tables.sql`
5. `analytics/03_create_analysis_views.sql`

Raw source data is intentionally not committed to Git.
