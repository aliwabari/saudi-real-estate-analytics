USE SaudiRealEstateAnalytics;
GO
-- Committed files and counts, including empty records and source warnings.
SELECT TargetTable, COUNT(*) AS FilesLoaded, SUM(SourceRows) AS SourceRows,
       SUM(BlankRows) AS BlankRows, SUM(LoadedRows) AS LoadedRows,
       SUM(RoundedCells) AS RoundedCells,
       SUM(DatePeriodMismatches) AS DatePeriodMismatches
FROM raw.IngestionFiles
GROUP BY TargetTable;

SELECT N'MOJ_Sales' AS TargetTable, COUNT_BIG(*) AS ActualRows FROM raw.MOJ_Sales
UNION ALL
SELECT N'REGA_Rentals', COUNT_BIG(*) FROM raw.REGA_Rentals
OPTION (MAXDOP 1);

-- Each row should show matching ExpectedRows and ActualRows.
SELECT f.IngestionFileID, f.SourcePath, f.LoadedRows AS ExpectedRows,
       COALESCE(s.ActualRows, r.ActualRows, 0) AS ActualRows
FROM raw.IngestionFiles f
LEFT JOIN (SELECT IngestionFileID, COUNT_BIG(*) AS ActualRows
           FROM raw.MOJ_Sales WHERE IngestionFileID IS NOT NULL GROUP BY IngestionFileID) s
    ON f.IngestionFileID=s.IngestionFileID AND f.TargetTable='MOJ_Sales'
LEFT JOIN (SELECT IngestionFileID, COUNT_BIG(*) AS ActualRows
           FROM raw.REGA_Rentals WHERE IngestionFileID IS NOT NULL GROUP BY IngestionFileID) r
    ON f.IngestionFileID=r.IngestionFileID AND f.TargetTable='REGA_Rentals'
ORDER BY f.SourcePath
OPTION (MAXDOP 1);

-- Review dates behind filenames without changing them.
SELECT f.SourcePath, MIN(s.GregorianDate) AS FirstDate,
       MAX(s.GregorianDate) AS LastDate, f.DatePeriodMismatches
FROM raw.IngestionFiles f
JOIN raw.MOJ_Sales s ON s.IngestionFileID=f.IngestionFileID
WHERE f.DatePeriodMismatches>0
GROUP BY f.SourcePath, f.DatePeriodMismatches
OPTION (MAXDOP 1);

-- Examples of retained source fields/precision.
SELECT TOP (10) IngestionFileID, SourceRowNumber, AverageValue, SourceExtraJson
FROM raw.REGA_Rentals WHERE SourceExtraJson IS NOT NULL
ORDER BY IngestionFileID, SourceRowNumber;
