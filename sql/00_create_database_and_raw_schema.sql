-- Run in SSMS before creating raw tables on a new SQL Server instance.
USE master;
GO
IF DB_ID(N'SaudiRealEstateAnalytics') IS NULL
    CREATE DATABASE SaudiRealEstateAnalytics;
GO
USE SaudiRealEstateAnalytics;
GO
IF SCHEMA_ID(N'raw') IS NULL EXEC(N'CREATE SCHEMA raw');
