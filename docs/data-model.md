# Data model

The project uses three SQL layers:

1. **raw** — source-shaped staging tables loaded from CSV.
2. **core** — cleaned relational model with surrogate keys and constraints.
3. **analytics** — flattened reporting views consumed by Power BI.

## Geography hierarchy

```text
Region
  └── City
       └── Neighborhood
```

## Sales model

`core.SaleTransaction` stores one retained sale transaction and links to:

- `core.Neighborhood`
- `core.SalePropertyClassification`

Confirmed rules:

- `TransactionReference` is unique.
- `PropertyCount > 0`.
- `Price > 0`.
- `Area` can be null; when populated it must be greater than zero.

## Rental model

`core.RentalIndicator` links to:

- `core.City`
- `core.RentalPropertyType`

Confirmed uniqueness key:

```text
Year + Quarter + CityID + RentalPropertyTypeID
```

## Power BI semantic model

The reporting model follows a star-style layout.

**Facts**
- FactSales
- FactRental

**Dimensions**
- Region
- City
- Neighborhood
- Property Classification
- Rental Property Type
- Date

Sales uses a full Gregorian date. Rental data is available at year/quarter grain, so time comparisons respect the lower rental granularity.
