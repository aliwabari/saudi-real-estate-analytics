-- Agreed source/staging business columns. No transaction-reference key assumption.
USE SaudiRealEstateAnalytics;
GO
IF OBJECT_ID(N'raw.MOJ_Sales', N'U') IS NULL
BEGIN
    CREATE TABLE raw.MOJ_Sales (
        Region NVARCHAR(100) NULL,
        City NVARCHAR(100) NULL,
        Neighborhood NVARCHAR(200) NULL,
        TransactionReference NVARCHAR(100) NULL,
        GregorianDate DATE NULL,
        HijriDate NVARCHAR(20) NULL,
        PropertyClassification NVARCHAR(100) NULL,
        PropertyCount INT NULL,
        Price DECIMAL(18,2) NULL,
        Area DECIMAL(18,2) NULL
    );
END;
IF OBJECT_ID(N'raw.REGA_Rentals', N'U') IS NULL
BEGIN
    CREATE TABLE raw.REGA_Rentals (
        Year INT NULL,
        Quarter INT NULL,
        Region NVARCHAR(100) NULL,
        City NVARCHAR(100) NULL,
        PropertyType NVARCHAR(150) NULL,
        TotalDeals INT NULL,
        AverageValue DECIMAL(18,2) NULL
    );
END;
