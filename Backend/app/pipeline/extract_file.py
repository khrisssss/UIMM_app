"""Source 1 - data file: the CSV of companies to enrich, prepared by the consultants.

Expected columns: siren (required), name and website (optional). Comma or semicolon separated,
UTF-8 (an Excel "CSV UTF-8" export works). Rows are returned as read; cleaning happens in aggregate.py.
"""
import csv
import logging
from pathlib import Path

logger = logging.getLogger("pipeline.file")


def extract_file(path: Path) -> list[dict]:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    with path.open(encoding="utf-8-sig", newline="") as handle:
        sample = handle.read(4096)
        handle.seek(0)
        delimiter = ";" if sample.count(";") > sample.count(",") else ","
        reader = csv.DictReader(handle, delimiter=delimiter)
        if reader.fieldnames is None:
            raise ValueError(f"The input file is empty: {path}")

        columns = {name.strip().lower() for name in reader.fieldnames if name}
        if "siren" not in columns:
            raise ValueError(f"The input file must have a 'siren' column, found: {sorted(columns)}")

        rows = []
        for line_number, raw_row in enumerate(reader, start=2):  # line 1 is the header
            row = {(key or "").strip().lower(): (value or "").strip() for key, value in raw_row.items()}
            rows.append({
                "line": line_number,
                "siren": row.get("siren", ""),
                "name": row.get("name", ""),
                "website": row.get("website", ""),
            })

    logger.info("File source: %s rows read from %s", len(rows), path.name)
    return rows
