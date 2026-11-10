"""Launch point of the public-data pipeline.

    python -m app.pipeline.run --input companies.csv

Steps: 1 file -> 2 database -> 3 API -> 4 big data -> 5 scraping -> aggregate -> save files -> load into PostgreSQL.
The input file is required; if another source fails, the run continues with the remaining
sources and the failure is logged and listed in the run summary.
Exit code: 0 success, 1 the run could not complete (nothing is loaded in that case).
"""
import argparse
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

from app.pipeline import config
from app.pipeline.aggregate import aggregate, save_outputs
from app.pipeline.extract_api import extract_api
from app.pipeline.extract_bigdata import count_active_by_naf, download_sirene, extract_bigdata
from app.pipeline.extract_database import extract_database
from app.pipeline.extract_file import extract_file
from app.pipeline.extract_scraping import extract_scraping
from app.pipeline.load import load

logger = logging.getLogger("pipeline")


def setup_logging(log_dir: Path) -> Path:
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"run_{datetime.now():%Y%m%d_%H%M%S}.log"
    formatter = logging.Formatter("%(asctime)s %(levelname)-7s %(name)s - %(message)s", "%H:%M:%S")
    root = logging.getLogger("pipeline")
    root.handlers.clear()
    root.setLevel(logging.INFO)
    root.propagate = False
    for handler in (logging.StreamHandler(sys.stdout), logging.FileHandler(log_file, encoding="utf-8")):
        handler.setFormatter(formatter)
        root.addHandler(handler)
    return log_file


def run(input_file: Path, sirene_file: Path | None = None, skip_bigdata=False, skip_scraping=False,
        load_into_database=True, output_dir: Path = config.OUTPUT_DIR) -> dict:
    started = time.perf_counter()
    source_errors = []

    # 1. File (required): the SIRENs to enrich
    file_rows = extract_file(input_file)

    # 2. Database: companies already in UIMM Boost, with their scores
    from app.database import SessionLocal  # imported here so tests can run without a configured database
    try:
        with SessionLocal() as session:
            database_rows = extract_database(session)
    except Exception as error:  # the database is optional for enrichment
        logger.error("Database source failed: %s", error)
        source_errors.append({"source": "database", "reason": str(error)})
        database_rows = []

    # Every SIREN that looks valid is sent to the public sources; aggregate.py does the full cleaning.
    from app.services.siren import normalize_siren
    candidate_sirens = []
    for value in [row["siren"] for row in file_rows] + [row["siren"] for row in database_rows]:
        try:
            siren = normalize_siren(value)
        except ValueError:
            continue
        if siren and siren not in candidate_sirens:
            candidate_sirens.append(siren)
    logger.info("%s distinct valid SIRENs to enrich", len(candidate_sirens))

    # 3. REST API
    api_records, api_errors = extract_api(candidate_sirens)
    source_errors += api_errors

    # 4. Big data: SIRENE stock (lookup + sector size)
    sirene_records, sector_counts = {}, {}
    if skip_bigdata:
        logger.info("Big data source skipped (--skip-bigdata)")
    else:
        try:
            parquet_path = Path(sirene_file) if sirene_file else download_sirene()
            sirene_records, connection = extract_bigdata(candidate_sirens, parquet_path)
            naf_codes = {record.get("naf_code") for record in list(api_records.values()) + list(sirene_records.values())}
            sector_counts = count_active_by_naf(connection, {code for code in naf_codes if code})
            connection.close()
            logger.info("Big data: sector size computed for %s NAF codes", len(sector_counts))
        except Exception as error:
            logger.error("Big data source failed: %s", error)
            source_errors.append({"source": "sirene", "reason": str(error)})

    # 5. Scraping: company websites listed in the file
    scraping_records = {}
    websites = {}
    for row in file_rows:
        try:
            siren = normalize_siren(row["siren"])
        except ValueError:
            continue
        if siren and row["website"] and siren not in websites:
            websites[siren] = row["website"] if row["website"].startswith("http") else "https://" + row["website"]
    if skip_scraping:
        logger.info("Scraping source skipped (--skip-scraping)")
    elif websites:
        scraping_records, scraping_errors = extract_scraping(websites)
        source_errors += scraping_errors

    # Aggregate, clean and save
    dataset, rejected = aggregate(file_rows, database_rows, api_records, sirene_records, sector_counts, scraping_records)
    summary = {
        "started_at": datetime.now().isoformat(timespec="seconds"),
        "input_file": str(input_file),
        "rows_in_file": len(file_rows),
        "companies_in_database": len(database_rows),
        "found_in_api": len(api_records),
        "found_in_sirene": len(sirene_records),
        "websites_scraped": sum(1 for record in scraping_records.values() if record.get("website_description")),
        "dataset_rows": len(dataset),
        "rejected_rows": len(rejected),
        "source_errors": source_errors,
    }

    # Load into PostgreSQL (one transaction)
    if load_into_database and dataset:
        with SessionLocal.begin() as session:
            summary["load"] = load(session, dataset)
    summary["duration_seconds"] = round(time.perf_counter() - started, 1)
    summary["output_files"] = save_outputs(dataset, rejected, summary, output_dir)
    logger.info("Done in %ss: %s rows in the dataset, %s rejected, %s source errors",
                summary["duration_seconds"], len(dataset), len(rejected), len(source_errors))
    return summary


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Enrich companies with official public data (SIRENE).")
    parser.add_argument("--input", required=True, type=Path, help="CSV with a 'siren' column (optional: name, website)")
    parser.add_argument("--sirene-file", type=Path, help="Local StockUniteLegale.parquet (otherwise downloaded once)")
    parser.add_argument("--skip-bigdata", action="store_true", help="Do not use the SIRENE stock file")
    parser.add_argument("--skip-scraping", action="store_true", help="Do not read company websites")
    parser.add_argument("--no-load", action="store_true", help="Write the CSV files only, do not import into PostgreSQL")
    args = parser.parse_args(argv)

    log_file = setup_logging(config.LOG_DIR)
    logger.info("Pipeline started; log file: %s", log_file)
    try:
        summary = run(args.input, args.sirene_file, args.skip_bigdata, args.skip_scraping, not args.no_load)
    except Exception as error:
        logger.exception("Pipeline stopped: %s", error)
        return 1
    for name, path in summary["output_files"].items():
        logger.info("Output %s: %s", name, path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
