"""Aggregation: merge the five sources into one clean dataset, one row per SIREN.

Rules, in order:
1. Corrupted entries are removed, with a reason: invalid SIREN (format or checksum),
   duplicate SIREN, SIREN unknown to both public sources.
2. Sources are merged field by field. The API is updated daily and the SIRENE stock monthly,
   so the API value wins and SIRENE fills the gaps.
3. Formats are made uniform: SIREN as 9 digits, NAF as "NN.NNX", dates as ISO dates, headcount code
   plus its INSEE label, active flag as a boolean, text trimmed, websites as https URLs.
4. RGPD: for a sole trader (legal form starting with 1) the name and address are a person's
   name and home address, and for a company in "partial diffusion" (status P) the person has
   opposed their publication: in both cases the name and address are removed.
"""
import csv
import json
import logging
import re
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse

from app.pipeline import config
from app.services.siren import normalize_siren

logger = logging.getLogger("pipeline.aggregate")

DATASET_COLUMNS = [
    "siren", "company_id", "name_in_file", "legal_name", "legal_form_code", "naf_code", "naf_section",
    "headcount_code", "headcount_label", "company_category", "creation_date", "is_active",
    "head_office_address", "postal_code", "city", "website", "website_description",
    "sector_active_companies", "scored_axes", "avg_score_percentage", "sources",
]

NAF_SECTIONS = [  # first two NAF digits -> section letter (NAF rév. 2)
    (1, 3, "A"), (5, 9, "B"), (10, 33, "C"), (35, 35, "D"), (36, 39, "E"), (41, 43, "F"), (45, 47, "G"),
    (49, 53, "H"), (55, 56, "I"), (58, 63, "J"), (64, 66, "K"), (68, 68, "L"), (69, 75, "M"), (77, 82, "N"),
    (84, 84, "O"), (85, 85, "P"), (86, 88, "Q"), (90, 93, "R"), (94, 96, "S"), (97, 98, "T"), (99, 99, "U"),
]


def clean_text(value) -> str | None:
    if value is None:
        return None
    text = re.sub(r"\s+", " ", str(value)).strip()
    return text or None


def normalize_naf(value) -> str | None:
    text = (clean_text(value) or "").upper().replace(" ", "")
    if re.fullmatch(r"\d{4}[A-Z]", text):
        text = f"{text[:2]}.{text[2:]}"
    return text if re.fullmatch(r"\d{2}\.\d{2}[A-Z]", text) else None


def naf_section(naf_code: str | None) -> str | None:
    if not naf_code:
        return None
    division = int(naf_code[:2])
    return next((letter for low, high, letter in NAF_SECTIONS if low <= division <= high), None)


def parse_date(value) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    for pattern in ("%Y-%m-%d", "%Y%m%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, pattern).date()
        except ValueError:
            continue
    return None


def normalize_headcount(value) -> str | None:
    code = clean_text(value)
    if code is None:
        return None
    code = code.zfill(2) if code.isdigit() else code.upper()
    return code if code in config.HEADCOUNT_LABELS else None


def normalize_website(value) -> str | None:
    text = clean_text(value)
    if not text:
        return None
    if not re.match(r"^https?://", text, re.IGNORECASE):
        text = "https://" + text
    parts = urlparse(text)
    if "." not in parts.netloc:
        return None
    return f"{parts.scheme.lower()}://{parts.netloc.lower()}{parts.path or '/'}"


def is_sole_trader(legal_form_code) -> bool:
    return str(legal_form_code or "").startswith("1")


def first_value(*values):
    return next((value for value in values if value not in (None, "")), None)


def aggregate(file_rows, database_rows, api_records, sirene_records, sector_counts, scraping_records):
    """Return (dataset, rejected). Each rejected entry says which source and why."""
    rejected = []
    wanted = {}  # siren -> {"file": row, "db": row}

    for row in file_rows:
        try:
            siren = normalize_siren(row["siren"])
        except ValueError as error:
            rejected.append({"source": "file", "line": row["line"], "siren": row["siren"], "reason": str(error)})
            continue
        if siren is None:
            rejected.append({"source": "file", "line": row["line"], "siren": "", "reason": "Missing SIREN."})
            continue
        if siren in wanted:
            rejected.append({"source": "file", "line": row["line"], "siren": siren,
                             "reason": f"Duplicate SIREN (first kept at line {wanted[siren]['file']['line']})."})
            continue
        wanted[siren] = {"file": row, "db": None}

    for row in database_rows:
        try:
            siren = normalize_siren(row["siren"])
        except ValueError as error:
            rejected.append({"source": "database", "line": f"company {row['company_id']}", "siren": row["siren"], "reason": str(error)})
            continue
        wanted.setdefault(siren, {"file": None, "db": None})["db"] = row

    dataset = []
    for siren, origin in wanted.items():
        api = api_records.get(siren) or {}
        sirene = sirene_records.get(siren) or {}
        if not api and not sirene:
            rejected.append({"source": "file" if origin["file"] else "database",
                             "line": origin["file"]["line"] if origin["file"] else f"company {origin['db']['company_id']}",
                             "siren": siren, "reason": "SIREN not found in the API nor in the SIRENE stock."})
            continue

        file_row, db_row = origin["file"] or {}, origin["db"] or {}
        scraped = scraping_records.get(siren) or {}
        legal_form = clean_text(first_value(api.get("legal_form_code"), sirene.get("legal_form_code")))
        naf = normalize_naf(first_value(api.get("naf_code"), sirene.get("naf_code")))
        headcount = normalize_headcount(first_value(api.get("headcount_code"), sirene.get("headcount_code")))
        state = clean_text(first_value(api.get("administrative_state"), sirene.get("administrative_state")))
        hide_identity = is_sole_trader(legal_form) or sirene.get("diffusion_status") == "P"

        sources = [name for name, present in (("file", file_row), ("database", db_row), ("api", api),
                                               ("sirene", sirene), ("scraping", scraped.get("website_description")))
                   if present]
        dataset.append({
            "siren": siren,
            "company_id": db_row.get("company_id"),
            "name_in_file": clean_text(file_row.get("name")),
            "legal_name": None if hide_identity else clean_text(first_value(api.get("legal_name"), sirene.get("legal_name"))),
            "legal_form_code": legal_form,
            "naf_code": naf,
            "naf_section": clean_text(api.get("naf_section")) or naf_section(naf),
            "headcount_code": headcount,
            "headcount_label": config.HEADCOUNT_LABELS.get(headcount) if headcount else None,
            "company_category": clean_text(first_value(api.get("company_category"), sirene.get("company_category"))),
            "creation_date": parse_date(first_value(api.get("creation_date"), sirene.get("creation_date"))),
            "is_active": None if state is None else state.upper() == "A",
            "head_office_address": None if hide_identity else clean_text(api.get("head_office_address")),
            "postal_code": clean_text(api.get("postal_code")),
            "city": clean_text(api.get("city")),
            "website": normalize_website(file_row.get("website")),
            "website_description": (clean_text(scraped.get("website_description")) or "")[:500] or None,
            "sector_active_companies": sector_counts.get(naf) if naf else None,
            "scored_axes": db_row.get("scored_axes"),
            "avg_score_percentage": db_row.get("avg_score_percentage"),
            "sources": ",".join(sources),
        })

    logger.info("Aggregation: %s rows kept, %s rejected", len(dataset), len(rejected))
    return dataset, rejected


def save_outputs(dataset, rejected, summary, output_dir: Path = config.OUTPUT_DIR) -> dict:
    """Write the final dataset, the rejected rows and a run summary. Returns the file paths."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "dataset": output_dir / "company_public_dataset.csv",
        "rejected": output_dir / "rejected_rows.csv",
        "summary": output_dir / "run_summary.json",
    }
    with paths["dataset"].open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=DATASET_COLUMNS)
        writer.writeheader()
        writer.writerows(dataset)
    with paths["rejected"].open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["source", "line", "siren", "reason"])
        writer.writeheader()
        writer.writerows(rejected)
    paths["summary"].write_text(json.dumps(summary, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return {name: str(path) for name, path in paths.items()}
