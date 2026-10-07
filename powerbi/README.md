# Power BI report

The final report is the presentation layer for the Saudi Real Estate Analytics project.

## Report pages

### 1. Executive / Market Overview
High-level KPIs and market trend:
- total sales transactions;
- total sales value;
- median sale price;
- average sale price;
- sales and rental activity over time.

### 2. Sales Market Analysis
Detailed sales analysis:
- transactions by city;
- transactions by property classification;
- average and median pricing;
- price distribution;
- price vs. area scatter analysis;
- outlier investigation.

### 3. Geographic Analysis
Geographic comparisons across region, city, and neighborhood.

### 4. Rental Market Analysis
Rental indicators by year/quarter, region, city, property type, total deals, and reported average rental value.

## Modeling notes

- Sales and rentals are separate fact tables.
- Geography dimensions are shared where possible.
- `DimDate` spans 2019-01-01 through 2025-12-31.
- Rental data is year/quarter grain and should not be interpreted as daily data.
- DAX measures are used for totals, averages, medians, and ranking.
- Power Query is used for model shaping and key replacement.

## Portfolio preview

The formatted case study with report captures is available here:

https://heyzine.com/flip-book/a90b80ff5f.html
