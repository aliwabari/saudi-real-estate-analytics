-- Historical: used by the earlier loader; not required by the simplified loader.
-- Ingestion metadata only. Existing business columns and data are retained.
-- Run in SaudiRealEstateAnalytics. The Python loader runs this automatically.
SET XACT_ABORT ON;
IF SCHEMA_ID(N'raw') IS NULL EXEC(N'CREATE SCHEMA raw');
IF OBJECT_ID(N'raw.MOJ_Sales', N'U') IS NULL
    THROW 51000, 'Create raw.MOJ_Sales before running ingestion.', 1;
IF OBJECT_ID(N'raw.REGA_Rentals', N'U') IS NULL
    THROW 51000, 'Create raw.REGA_Rentals before running ingestion.', 1;

IF OBJECT_ID(N'raw.IngestionFiles', N'U') IS NULL
BEGIN
    CREATE TABLE raw.IngestionFiles (
        IngestionFileID BIGINT IDENTITY(1,1) PRIMARY KEY,
        TargetTable VARCHAR(30) NOT NULL,
        SourcePath NVARCHAR(400) NOT NULL,
        FileSHA256 CHAR(64) NOT NULL,
        FileBytes BIGINT NOT NULL,
        SourceRows BIGINT NOT NULL,
        BlankRows BIGINT NOT NULL,
        LoadedRows BIGINT NOT NULL,
        RoundedCells BIGINT NOT NULL,
        DatePeriodMismatches BIGINT NOT NULL,
        HeaderJSON NVARCHAR(MAX) NOT NULL,
        LoaderVersion VARCHAR(20) NOT NULL,
        LoadedAtUTC DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),
        CONSTRAINT UQ_IngestionFiles_Path UNIQUE (TargetTable, SourcePath),
        CONSTRAINT UQ_IngestionFiles_Hash UNIQUE (TargetTable, FileSHA256),
        CONSTRAINT CK_IngestionFiles_Count CHECK (SourceRows = BlankRows + LoadedRows)
    );
END;
GO
IF COL_LENGTH(N'raw.MOJ_Sales', N'IngestionFileID') IS NULL
    ALTER TABLE raw.MOJ_Sales ADD IngestionFileID BIGINT NULL;
IF COL_LENGTH(N'raw.MOJ_Sales', N'SourceRowNumber') IS NULL
    ALTER TABLE raw.MOJ_Sales ADD SourceRowNumber INT NULL;
IF COL_LENGTH(N'raw.MOJ_Sales', N'SourceExtraJson') IS NULL
    ALTER TABLE raw.MOJ_Sales ADD SourceExtraJson NVARCHAR(MAX) NULL;
IF COL_LENGTH(N'raw.REGA_Rentals', N'IngestionFileID') IS NULL
    ALTER TABLE raw.REGA_Rentals ADD IngestionFileID BIGINT NULL;
IF COL_LENGTH(N'raw.REGA_Rentals', N'SourceRowNumber') IS NULL
    ALTER TABLE raw.REGA_Rentals ADD SourceRowNumber INT NULL;
IF COL_LENGTH(N'raw.REGA_Rentals', N'SourceExtraJson') IS NULL
    ALTER TABLE raw.REGA_Rentals ADD SourceExtraJson NVARCHAR(MAX) NULL;
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'raw.MOJ_Sales') AND name = N'UX_MOJ_Sales_SourceRow')
    CREATE UNIQUE INDEX UX_MOJ_Sales_SourceRow ON raw.MOJ_Sales(IngestionFileID, SourceRowNumber) WHERE IngestionFileID IS NOT NULL;
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'raw.REGA_Rentals') AND name = N'UX_REGA_Rentals_SourceRow')
    CREATE UNIQUE INDEX UX_REGA_Rentals_SourceRow ON raw.REGA_Rentals(IngestionFileID, SourceRowNumber) WHERE IngestionFileID IS NOT NULL;
IF OBJECT_ID(N'raw.FK_MOJ_Sales_IngestionFiles', N'F') IS NULL
    ALTER TABLE raw.MOJ_Sales ADD CONSTRAINT FK_MOJ_Sales_IngestionFiles
        FOREIGN KEY (IngestionFileID) REFERENCES raw.IngestionFiles(IngestionFileID);
IF OBJECT_ID(N'raw.FK_REGA_Rentals_IngestionFiles', N'F') IS NULL
    ALTER TABLE raw.REGA_Rentals ADD CONSTRAINT FK_REGA_Rentals_IngestionFiles
        FOREIGN KEY (IngestionFileID) REFERENCES raw.IngestionFiles(IngestionFileID);
