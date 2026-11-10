"""Source 5 - big data: the national SIRENE stock of legal units (INSEE, Parquet, ~29 million rows).

The file is too large to load in memory with pandas. DuckDB queries the Parquet file directly:
it only reads the columns a query needs (columnar format) and skips row groups that cannot match
(predicate pushdown), so a full scan of the 29 million rows takes seconds on a laptop.
"""
import logging
import shutil
from pathlib import Path

import duckdb
import requests

from app.pipeline import config

logger = logging.getLogger("pipeline.bigdata")

REQUIRED_COLUMNS = {
    "siren", "denominationUniteLegale", "categorieJuridiqueUniteLegale", "activitePrincipaleUniteLegale",
    "trancheEffectifsUniteLegale", "categorieEntreprise", "dateCreationUniteLegale", "etatAdministratifUniteLegale",
}


def download_sirene(url: str = config.SIRENE_PARQUET_URL, destination: Path = config.SIRENE_LOCAL_FILE,
                    session: requests.Session | None = None) -> Path:
    """Download the Parquet file once; later runs reuse the local copy (delete it to refresh)."""
    destination = Path(destination)
    if destination.exists() and destination.stat().st_size > 0:
        logger.info("Big data: reusing local SIRENE file %s (%.0f MB)", destination, destination.stat().st_size / 1e6)
        return destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(".part")
    session = session or requests.Session()
    logger.info("Big data: downloading SIRENE stock from %s (about 700 MB, a few minutes)", url)
    with session.get(url, stream=True, timeout=60, headers={"User-Agent": config.USER_AGENT}) as response:
        response.raise_for_status()
        with partial.open("wb") as handle:
            shutil.copyfileobj(response.raw, handle, length=8 * 1024 * 1024)
    partial.rename(destination)  # only a complete download gets the final name
    logger.info("Big data: download complete (%.0f MB)", destination.stat().st_size / 1e6)
    return destination


def open_sirene(parquet_path: Path) -> duckdb.DuckDBPyConnection:
    """Open DuckDB on the file and check it really is the legal-units stock."""
    connection = duckdb.connect()
    escaped = str(parquet_path).replace("'", "''")
    connection.execute(f"CREATE VIEW sirene AS SELECT * FROM read_parquet('{escaped}')")
    columns = {row[0] for row in connection.execute("DESCRIBE sirene").fetchall()}
    missing = REQUIRED_COLUMNS - columns
    if missing:
        connection.close()
        raise ValueError(f"{parquet_path} is not the SIRENE 'StockUniteLegale' file; missing columns: {sorted(missing)}")
    return connection


def lookup_companies(connection, sirens: list[str]) -> dict:
    """Official SIRENE record of each wanted SIREN (one columnar scan with a join)."""
    connection.execute("CREATE OR REPLACE TEMP TABLE wanted_siren (siren VARCHAR)")
    connection.executemany("INSERT INTO wanted_siren VALUES (?)", [[siren] for siren in sirens])
    # 'P' = partial diffusion: the person opposed the publication of their personal data (RGPD).
    columns = {row[0] for row in connection.execute("DESCRIBE sirene").fetchall()}
    diffusion = "s.statutDiffusionUniteLegale" if "statutDiffusionUniteLegale" in columns else "NULL"
    rows = connection.execute(f"""
        SELECT s.siren,
               s.denominationUniteLegale        AS legal_name,
               s.categorieJuridiqueUniteLegale  AS legal_form_code,
               s.activitePrincipaleUniteLegale  AS naf_code,
               s.trancheEffectifsUniteLegale    AS headcount_code,
               s.categorieEntreprise            AS company_category,
               s.dateCreationUniteLegale        AS creation_date,
               s.etatAdministratifUniteLegale   AS administrative_state,
               {diffusion}                      AS diffusion_status
        FROM sirene AS s
        JOIN wanted_siren AS w ON CAST(s.siren AS VARCHAR) = w.siren
    """).fetchall()
    names = ["siren", "legal_name", "legal_form_code", "naf_code", "headcount_code",
             "company_category", "creation_date", "administrative_state", "diffusion_status"]
    return {str(row[0]): dict(zip(names, row)) for row in rows}


def count_active_by_naf(connection, naf_codes: set[str]) -> dict:
    """Sector context: number of active companies in France for each NAF code (full scan + GROUP BY)."""
    if not naf_codes:
        return {}
    connection.execute("CREATE OR REPLACE TEMP TABLE wanted_naf (naf VARCHAR)")
    connection.executemany("INSERT INTO wanted_naf VALUES (?)", [[code] for code in sorted(naf_codes)])
    rows = connection.execute("""
        SELECT activitePrincipaleUniteLegale AS naf, COUNT(*) AS active_companies
        FROM sirene
        WHERE etatAdministratifUniteLegale = 'A'
          AND activitePrincipaleUniteLegale IN (SELECT naf FROM wanted_naf)
        GROUP BY activitePrincipaleUniteLegale
    """).fetchall()
    return {naf: count for naf, count in rows}


def extract_bigdata(sirens: list[str], parquet_path: Path) -> tuple[dict, object]:
    """Return ({siren: record}, open DuckDB connection for the sector counts)."""
    connection = open_sirene(parquet_path)
    total_rows = connection.execute("SELECT COUNT(*) FROM sirene").fetchone()[0]
    records = lookup_companies(connection, sirens)
    logger.info("Big data source: %s/%s SIRENs found among %s SIRENE rows", len(records), len(sirens), f"{total_rows:,}")
    return records, connection
