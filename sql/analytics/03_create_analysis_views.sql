USE SaudiRealEstateAnalytics;
GO

IF SCHEMA_ID(N'analytics') IS NULL
    EXEC(N'CREATE SCHEMA analytics');
GO

CREATE OR ALTER VIEW analytics.vw_SalesAnalysis
AS
SELECT
    st.SaleTransactionID,
    st.TransactionReference,
    st.GregorianDate,
    r.RegionName,
    c.CityName,
    n.NeighborhoodName,
    spc.ClassificationName,
    st.PropertyCount,
    st.Area,
    st.Price
FROM core.SaleTransaction AS st
INNER JOIN core.Neighborhood AS n
    ON st.NeighborhoodID = n.NeighborhoodID
INNER JOIN core.City AS c
    ON n.CityID = c.CityID
INNER JOIN core.Region AS r
    ON c.RegionID = r.RegionID
INNER JOIN core.SalePropertyClassification AS spc
    ON st.ClassificationID = spc.ClassificationID;
GO

CREATE OR ALTER VIEW analytics.vw_RentalAnalysis
AS
SELECT
    ri.RentalIndicatorID,
    ri.Year,
    ri.Quarter,
    r.RegionName,
    c.CityName,
    rpt.PropertyTypeName,
    ri.TotalDeals,
    ri.AverageValue
FROM core.RentalIndicator AS ri
INNER JOIN core.City AS c
    ON ri.CityID = c.CityID
INNER JOIN core.Region AS r
    ON c.RegionID = r.RegionID
INNER JOIN core.RentalPropertyType AS rpt
    ON ri.RentalPropertyTypeID = rpt.RentalPropertyTypeID;
GO
