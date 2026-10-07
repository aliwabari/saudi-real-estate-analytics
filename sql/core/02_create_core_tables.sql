USE SaudiRealEstateAnalytics;
GO

IF SCHEMA_ID(N'core') IS NULL
    EXEC(N'CREATE SCHEMA core');
GO

IF OBJECT_ID(N'core.Region', N'U') IS NULL
BEGIN
    CREATE TABLE core.Region (
        RegionID INT IDENTITY(1,1) PRIMARY KEY,
        RegionName NVARCHAR(100) NOT NULL UNIQUE
    );
END;
GO

IF OBJECT_ID(N'core.City', N'U') IS NULL
BEGIN
    CREATE TABLE core.City (
        CityID INT IDENTITY(1,1) PRIMARY KEY,
        CityName NVARCHAR(100) NOT NULL,
        RegionID INT NOT NULL,
        CONSTRAINT FK_City_Region
            FOREIGN KEY (RegionID) REFERENCES core.Region(RegionID),
        CONSTRAINT UQ_City UNIQUE (RegionID, CityName)
    );
END;
GO

IF OBJECT_ID(N'core.Neighborhood', N'U') IS NULL
BEGIN
    CREATE TABLE core.Neighborhood (
        NeighborhoodID INT IDENTITY(1,1) PRIMARY KEY,
        NeighborhoodName NVARCHAR(200) NOT NULL,
        CityID INT NOT NULL,
        CONSTRAINT FK_Neighborhood_City
            FOREIGN KEY (CityID) REFERENCES core.City(CityID),
        CONSTRAINT UQ_Neighborhood UNIQUE (CityID, NeighborhoodName)
    );
END;
GO

IF OBJECT_ID(N'core.SalePropertyClassification', N'U') IS NULL
BEGIN
    CREATE TABLE core.SalePropertyClassification (
        ClassificationID INT IDENTITY(1,1) PRIMARY KEY,
        ClassificationName NVARCHAR(100) NOT NULL UNIQUE
    );
END;
GO

IF OBJECT_ID(N'core.RentalPropertyType', N'U') IS NULL
BEGIN
    CREATE TABLE core.RentalPropertyType (
        RentalPropertyTypeID INT IDENTITY(1,1) PRIMARY KEY,
        PropertyTypeName NVARCHAR(150) NOT NULL UNIQUE
    );
END;
GO

IF OBJECT_ID(N'core.SaleTransaction', N'U') IS NULL
BEGIN
    CREATE TABLE core.SaleTransaction (
        SaleTransactionID BIGINT IDENTITY(1,1) PRIMARY KEY,
        TransactionReference NVARCHAR(100) NOT NULL UNIQUE,
        NeighborhoodID INT NOT NULL,
        ClassificationID INT NOT NULL,
        GregorianDate DATE NOT NULL,
        HijriDate NVARCHAR(20) NULL,
        PropertyCount INT NOT NULL,
        Area DECIMAL(18,2) NULL,
        Price DECIMAL(18,2) NOT NULL,

        CONSTRAINT FK_SaleTransaction_Neighborhood
            FOREIGN KEY (NeighborhoodID) REFERENCES core.Neighborhood(NeighborhoodID),
        CONSTRAINT FK_SaleTransaction_Classification
            FOREIGN KEY (ClassificationID) REFERENCES core.SalePropertyClassification(ClassificationID),
        CONSTRAINT CK_SaleTransaction_PropertyCount CHECK (PropertyCount > 0),
        CONSTRAINT CK_SaleTransaction_Area CHECK (Area IS NULL OR Area > 0),
        CONSTRAINT CK_SaleTransaction_Price CHECK (Price > 0)
    );
END;
GO

IF OBJECT_ID(N'core.RentalIndicator', N'U') IS NULL
BEGIN
    CREATE TABLE core.RentalIndicator (
        RentalIndicatorID BIGINT IDENTITY(1,1) PRIMARY KEY,
        Year INT NOT NULL,
        Quarter INT NOT NULL,
        CityID INT NOT NULL,
        RentalPropertyTypeID INT NOT NULL,
        TotalDeals INT NULL,
        AverageValue DECIMAL(18,2) NULL,

        CONSTRAINT FK_RentalIndicator_City
            FOREIGN KEY (CityID) REFERENCES core.City(CityID),
        CONSTRAINT FK_RentalIndicator_PropertyType
            FOREIGN KEY (RentalPropertyTypeID) REFERENCES core.RentalPropertyType(RentalPropertyTypeID),
        CONSTRAINT CK_RentalIndicator_Quarter CHECK (Quarter BETWEEN 1 AND 4),
        CONSTRAINT UQ_RentalIndicator UNIQUE (Year, Quarter, CityID, RentalPropertyTypeID)
    );
END;
GO
