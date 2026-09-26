-- إعداد المشروع على جهاز جديد. قاعدة بياناتك الحالية موجودة بالفعل.
-- شروط IF تمنع محاولة إنشاء شيء موجود، ولا تحذف أو تعدّل البيانات.
USE master;
GO

IF DB_ID(N'SaudiRealEstateAnalytics') IS NULL
    CREATE DATABASE SaudiRealEstateAnalytics;
GO

-- اختيار قاعدة البيانات التي ستحتوي على السكيما والجداول.
USE SaudiRealEstateAnalytics;
GO

-- raw: جداول استقبال البيانات من ملفات CSV.
IF SCHEMA_ID(N'raw') IS NULL
    EXEC(N'CREATE SCHEMA raw');

-- core: مخصصة لاحقًا للجداول بعد التنظيف والتنظيم؛ لا ننشئ جداولها الآن.
IF SCHEMA_ID(N'core') IS NULL
    EXEC(N'CREATE SCHEMA core');

-- EXEC ينفّذ CREATE SCHEMA في دفعة مستقلة كما يتطلب SQL Server.
