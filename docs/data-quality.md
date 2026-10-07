# Data quality and profiling

The raw datasets were profiled before normalization so issues would not silently flow into the analytical model.

## MOJ sales

Key findings:

- duplicate `TransactionReference` values;
- inconsistent Arabic region spellings;
- `HijriDate` mostly blank, zero, or unavailable;
- valid transactions with `Area = 0`;
- extreme price outliers;
- repeated unusually large values in Riyadh / Al-Aqiq on 2020-05-14;
- the imported 2025 Q2 file contains Gregorian dates from April–June 2024, so the original dates were preserved.

## REGA rentals

The first duplicate check was too broad. The intended analytical grain became:

```text
Year + Quarter + City + Property Type
```

Adding City resolved the duplicate-key issue for the final rental model.

## Core decisions

- Sales and rentals remain separate facts because their grains differ.
- Gregorian date is used as the primary reporting date for sales.
- Zero or invalid area values are excluded from price-per-area interpretation.
- Mean and median sale price are both reported because outliers materially affect the mean.
- Rental deal counts are summed from the source indicator measure rather than counting rows.

## Duplicate handling

Duplicate sale references are ranked using `ROW_NUMBER()` and only one row is retained for the core transaction table.

```sql
ROW_NUMBER() OVER (
    PARTITION BY TransactionReference
    ORDER BY TransactionReference
) AS rn
```
