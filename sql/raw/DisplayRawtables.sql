-- استعلامات قراءة فقط: عرض عينة من البيانات ومعرفة عدد الصفوف.
USE SaudiRealEstateAnalytics;
GO

-- عينة من 10 صفوف مبيعات؛ TOP بدون ORDER BY لا يضمن ترتيبًا معينًا.
SELECT TOP (10) *
FROM raw.MOJ_Sales;

-- عينة من 10 صفوف إيجارات، بدل عرض الجدول كاملًا.
SELECT TOP (10) *
FROM raw.REGA_Rentals;

-- عدد الصفوف الموجودة في كل جدول.
SELECT COUNT(*) AS SalesRows
FROM raw.MOJ_Sales;

SELECT COUNT(*) AS RentalRows
FROM raw.REGA_Rentals;
