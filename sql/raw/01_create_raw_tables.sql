-- تعريف الجدولين الأساسيين لاستقبال CSV. شغّله بعد ملف إنشاء قاعدة البيانات.
USE SaudiRealEstateAnalytics;
GO

-- كل صف يمثل صفقة بيع واحدة. ننشئ الجدول فقط إذا لم يكن موجودًا.
-- لا نضع مفتاحًا أساسيًا على TransactionReference قبل اختبار تفرّده.
IF OBJECT_ID(N'raw.MOJ_Sales', N'U') IS NULL
BEGIN
    CREATE TABLE raw.MOJ_Sales (
        -- NVARCHAR يدعم أسماء المناطق والمدن والأحياء باللغة العربية.
        Region NVARCHAR(100) NULL,
        City NVARCHAR(100) NULL,
        Neighborhood NVARCHAR(200) NULL,
        TransactionReference NVARCHAR(100) NULL,
        GregorianDate DATE NULL,
        HijriDate NVARCHAR(20) NULL,
        PropertyClassification NVARCHAR(100) NULL,
        PropertyCount INT NULL,
        -- DECIMAL(18,2): أرقام عشرية بمنزلتين بعد الفاصلة.
        Price DECIMAL(18,2) NULL,
        Area DECIMAL(18,2) NULL
    );
END;
GO

-- كل صف يمثل مؤشر إيجارات لسنة وربع ومنطقة ومدينة ونوع عقار.
-- يبقى منفصلًا عن المبيعات لأن مستوى تفصيل البيانات مختلف.
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

-- NULL يسمح بترك القيمة فارغة إذا لم يوفرها المصدر.
-- هذه الأوامر لا تغيّر تعريف جدول موجود ولا تعيد إدخال بياناته.
