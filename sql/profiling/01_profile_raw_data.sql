USE SaudiRealEstateAnalytics;
GO

/* Row counts */
SELECT COUNT(*) AS SalesRows
FROM raw.MOJ_Sales;

SELECT COUNT(*) AS RentalRows
FROM raw.REGA_Rentals;


/* Duplicate sale references */
SELECT TOP (40)
    TransactionReference,
    COUNT(*) AS DuplicateCount
FROM raw.MOJ_Sales
WHERE TransactionReference IS NOT NULL
GROUP BY TransactionReference
HAVING COUNT(*) > 1
ORDER BY DuplicateCount DESC, TransactionReference;


/* Region distribution */
SELECT
    Region,
    COUNT(*) AS RowCount
FROM raw.MOJ_Sales
GROUP BY Region
ORDER BY RowCount DESC;


/* Missing and zero-value checks */
SELECT
    SUM(CASE WHEN TransactionReference IS NULL OR LTRIM(RTRIM(TransactionReference)) = '' THEN 1 ELSE 0 END) AS MissingTransactionReference,
    SUM(CASE WHEN GregorianDate IS NULL THEN 1 ELSE 0 END) AS MissingGregorianDate,
    SUM(CASE WHEN HijriDate IS NULL OR LTRIM(RTRIM(HijriDate)) IN ('', '0') THEN 1 ELSE 0 END) AS MissingOrZeroHijriDate,
    SUM(CASE WHEN Area IS NULL THEN 1 ELSE 0 END) AS MissingArea,
    SUM(CASE WHEN Area = 0 THEN 1 ELSE 0 END) AS ZeroArea,
    SUM(CASE WHEN Price IS NULL OR Price <= 0 THEN 1 ELSE 0 END) AS InvalidPrice
FROM raw.MOJ_Sales;


/* Highest sale prices for outlier review */
SELECT TOP (100)
    TransactionReference,
    GregorianDate,
    Region,
    City,
    Neighborhood,
    PropertyClassification,
    Area,
    Price
FROM raw.MOJ_Sales
WHERE Price IS NOT NULL
ORDER BY Price DESC;


/* Rental uniqueness at the confirmed grain */
SELECT
    Year,
    Quarter,
    Region,
    City,
    PropertyType,
    COUNT(*) AS DuplicateCount
FROM raw.REGA_Rentals
GROUP BY Year, Quarter, Region, City, PropertyType
HAVING COUNT(*) > 1
ORDER BY DuplicateCount DESC, Year, Quarter, Region, City, PropertyType;
