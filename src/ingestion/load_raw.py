"""Validate or load all MOJ sales and REGA rental files. Default: validate only."""

import argparse
import json
import logging
import os
import re
import sys
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

import pyodbc

from source_formats import COLUMNS, DECIMAL_COLUMNS, INTEGER_COLUMNS, TEXT_LENGTHS
from source_formats import discover, file_hash, inspect_file, read_rows

ROOT = Path(__file__).resolve().parents[2]
VERSION = "1.0.0"


def connect():
    # A connection string may be supplied by the environment; never log it.
    value = os.environ.get("PEAK_SQL_CONNECTION_STRING")
    if not value:
        value = (
            "DRIVER={ODBC Driver 18 for SQL Server};SERVER=localhost;"
            "DATABASE=SaudiRealEstateAnalytics;Trusted_Connection=yes;"
            "Encrypt=yes;TrustServerCertificate=yes;"
        )
    return pyodbc.connect(value, timeout=10)


def acquire_lock(connection):
    result = connection.execute("""
        SET NOCOUNT ON;
        DECLARE @result int;
        EXEC @result = sys.sp_getapplock @Resource=N'PeakRawIngestion',
             @LockMode='Exclusive', @LockOwner='Session', @LockTimeout=0;
        SELECT @result;
    """).fetchval()
    if result < 0:
        raise RuntimeError("Another ingestion process is running")
    connection.commit()


def check_schema(connection):
    """Fail rather than allowing SQL Server to truncate or silently change types."""
    for target, columns in COLUMNS.items():
        actual = {r[0]: tuple(r[1:]) for r in connection.execute("""
            SELECT c.name, t.name, c.max_length, c.precision, c.scale, c.is_nullable
            FROM sys.columns c JOIN sys.types t ON c.user_type_id=t.user_type_id
            WHERE c.object_id=OBJECT_ID(?)
        """, f"raw.{target}")}
        for column in columns:
            if column in TEXT_LENGTHS:
                expected = ("nvarchar", TEXT_LENGTHS[column] * 2, 0, 0, True)
            elif column in INTEGER_COLUMNS:
                expected = ("int", 4, 10, 0, True)
            elif column in DECIMAL_COLUMNS:
                expected = ("decimal", 9, 18, 2, True)
            else:
                expected = ("date", 3, 10, 0, True)
            if actual.get(column) != expected:
                raise RuntimeError(f"Schema mismatch for raw.{target}.{column}: {actual.get(column)}")
        if "IngestionFileID" not in actual:
            if connection.execute(f"SELECT COUNT_BIG(*) FROM raw.[{target}]").fetchval():
                raise RuntimeError(f"raw.{target} contains untracked rows; manual review required")


def prepare_tracking(connection):
    sql = (ROOT / "sql/raw/02_ingestion_tracking.sql").read_text(encoding="utf-8")
    for batch in re.split(r"(?im)^GO\s*$", sql):
        if batch.strip():
            connection.execute(batch)
    connection.commit()


def reconcile(connection):
    """Detect manual deletes or inserts before trusting the file ledger."""
    for target in COLUMNS:
        if connection.execute(
            f"SELECT COUNT_BIG(*) FROM raw.[{target}] WHERE IngestionFileID IS NULL OR SourceRowNumber IS NULL OPTION (MAXDOP 1)"
        ).fetchval():
            raise RuntimeError(f"Untracked rows exist in raw.{target}; refusing to append")
        mismatches = connection.execute(f"""
            SELECT f.IngestionFileID FROM raw.IngestionFiles f
            LEFT JOIN (SELECT IngestionFileID, COUNT_BIG(*) AS n FROM raw.[{target}]
                       WHERE IngestionFileID IS NOT NULL
                       GROUP BY IngestionFileID) r ON r.IngestionFileID=f.IngestionFileID
            WHERE f.TargetTable=? AND f.LoadedRows<>COALESCE(r.n,0)
            OPTION (MAXDOP 1)
        """, target).fetchall()
        if mismatches:
            raise RuntimeError(f"File ledger and row counts disagree for raw.{target}")


def already_loaded(connection, target, relative, digest):
    row = connection.execute(
        "SELECT FileSHA256 FROM raw.IngestionFiles WHERE TargetTable=? AND SourcePath=?",
        target, relative,
    ).fetchone()
    if row:
        if row[0] != digest:
            raise RuntimeError(f"Previously loaded file changed: {relative}. Review before reloading.")
        return True
    return connection.execute(
        "SELECT IngestionFileID FROM raw.IngestionFiles WHERE TargetTable=? AND FileSHA256=?",
        target, digest,
    ).fetchone() is not None


def input_sizes(target):
    sizes = []
    for column in COLUMNS[target]:
        if column in TEXT_LENGTHS:
            sizes.append((pyodbc.SQL_WVARCHAR, TEXT_LENGTHS[column], 0))
        elif column in INTEGER_COLUMNS:
            sizes.append((pyodbc.SQL_INTEGER, 0, 0))
        elif column in DECIMAL_COLUMNS:
            sizes.append((pyodbc.SQL_DECIMAL, 18, 2))
        else:
            sizes.append((pyodbc.SQL_TYPE_DATE, 0, 0))
    return sizes + [(pyodbc.SQL_BIGINT, 0, 0), (pyodbc.SQL_INTEGER, 0, 0)]


def insert_file(connection, target, path, stats, batch_size):
    """Rows and successful-file ledger commit together, or both roll back."""
    relative = path.relative_to(ROOT).as_posix()
    if file_hash(path) != stats["sha256"]:
        raise ValueError("Source changed since preflight")
    file_id = connection.execute("""
        INSERT raw.IngestionFiles
        (TargetTable,SourcePath,FileSHA256,FileBytes,SourceRows,BlankRows,LoadedRows,
         RoundedCells,DatePeriodMismatches,HeaderJSON,LoaderVersion)
        OUTPUT inserted.IngestionFileID
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """, target, relative, stats["sha256"], path.stat().st_size, stats["source_rows"],
        stats["blank_rows"], stats["loaded_rows"], stats["rounded_cells"],
        stats["date_period_mismatches"], json.dumps(stats["headers"], ensure_ascii=False), VERSION
    ).fetchval()
    columns = list(COLUMNS[target]) + ["IngestionFileID", "SourceRowNumber", "SourceExtraJson"]
    sql = f"INSERT raw.[{target}] ({','.join('[' + c + ']' for c in columns)}) VALUES ({','.join('?' for _ in columns)})"
    cursor = connection.cursor()
    cursor.fast_executemany = True
    batch = []
    observed = {}

    def flush():
        # Explicit buffer sizes avoid first-row NULL/short-text inference problems.
        json_size = max(1, max(len((r[-1] or "").encode("utf-16-le")) // 2 for r in batch))
        cursor.setinputsizes(input_sizes(target) + [(pyodbc.SQL_WVARCHAR, json_size, 0)])
        cursor.executemany(sql, batch)
        batch.clear()

    for number, values, extras in read_rows(path, target, observed):
        batch.append(values + (file_id, number, extras))
        if len(batch) == batch_size:
            flush()
    if batch:
        flush()
    cursor.close()
    inserted = connection.execute(
        f"SELECT COUNT_BIG(*) FROM raw.[{target}] WHERE IngestionFileID=?", file_id
    ).fetchval()
    if inserted != stats["loaded_rows"] or any(observed[k] != stats[k] for k in observed):
        raise RuntimeError("CSV count or contents changed during load")
    if file_hash(path) != stats["sha256"]:
        raise RuntimeError("Source changed during load")
    connection.commit()
    return inserted


def run(args, report):
    files = discover(ROOT)
    logging.info("Discovered %s source files", len(files))
    validated = []
    for target, path in files:
        entry = {"target": target, "file": path.name}
        report["files"].append(entry)
        try:
            entry.update(inspect_file(path, target))
            entry["status"] = "validated"
            validated.append((target, path, entry))
            logging.info("Validated %s: %s data rows, %s blank records", path.name,
                         entry["loaded_rows"], entry["blank_rows"])
            if entry["date_period_mismatches"]:
                logging.warning("%s: %s dates disagree with filename; retained as supplied",
                                path.name, entry["date_period_mismatches"])
        except Exception as error:
            entry.update(status="validation_failed", error=str(error))
            logging.error("Validation failed for %s: %s", path.name, error)
    if any(f["status"] == "validation_failed" for f in report["files"]):
        raise RuntimeError("Preflight failed; no database changes were made. See report.")
    if not args.load:
        return
    with closing(connect()) as connection:
        connection.timeout = 120
        acquire_lock(connection)
        check_schema(connection)
        prepare_tracking(connection)
        reconcile(connection)
        # Check every path before beginning any file load.
        for target, path, stats in validated:
            if already_loaded(connection, target, path.relative_to(ROOT).as_posix(), stats["sha256"]):
                stats["status"] = "skipped_already_loaded"
        connection.commit()
        for target, path, stats in validated:
            if stats["status"] == "skipped_already_loaded":
                logging.info("Skipped previously loaded file: %s", path.name)
                continue
            try:
                # Recheck to handle duplicate content within the current discovery set.
                if already_loaded(connection, target, path.relative_to(ROOT).as_posix(), stats["sha256"]):
                    stats["status"] = "skipped_already_loaded"
                    continue
                inserted = insert_file(connection, target, path, stats, args.batch_size)
                stats.update(status="loaded", inserted_rows=inserted)
                logging.info("Loaded %s: %s rows committed", path.name, inserted)
            except Exception as error:
                connection.rollback()
                stats.update(status="load_failed", error=str(error))
                raise
        reconcile(connection)
        report["database_counts"] = {
            target: connection.execute(f"SELECT COUNT_BIG(*) FROM raw.[{target}]").fetchval()
            for target in COLUMNS
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--load", action="store_true", help="Commit validated files to SQL Server")
    parser.add_argument("--batch-size", type=int, default=2000)
    args = parser.parse_args()
    if not 1 <= args.batch_size <= 10000:
        parser.error("--batch-size must be between 1 and 10000")
    logs = ROOT / "logs"
    logs.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.StreamHandler(), logging.FileHandler(logs / f"ingestion-{stamp}.log", encoding="utf-8")])
    report = {"started_utc": stamp, "mode": "load" if args.load else "validate", "files": []}
    code = 0
    try:
        run(args, report)
        report["status"] = "success"
    except Exception as error:
        report.update(status="failed", error=str(error))
        logging.error("Ingestion stopped: %s", error)
        code = 1
    finally:
        report_path = logs / f"ingestion-{stamp}.json"
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        logging.info("Report: %s", report_path.name)
    return code


if __name__ == "__main__":
    sys.exit(main())
