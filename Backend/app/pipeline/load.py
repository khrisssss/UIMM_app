"""Load: import the clean dataset into PostgreSQL (table company_public_data).

Upsert on the SIREN: a new SIREN is inserted, a known SIREN is updated, so the pipeline can be
run again every month without creating duplicates. Everything is saved in one transaction.
"""
import logging
from datetime import datetime, timezone

from app.models.company_public_data import CompanyPublicData

logger = logging.getLogger("pipeline.load")

TABLE_FIELDS = [
    "legal_name", "legal_form_code", "naf_code", "naf_section", "headcount_code", "headcount_label",
    "company_category", "creation_date", "is_active", "head_office_address", "postal_code", "city",
    "website", "website_description", "sector_active_companies", "sources",
]


def load(session, dataset: list[dict]) -> dict:
    """Upsert the rows. The caller commits (or rolls back) the transaction."""
    inserted = updated = 0
    for row in dataset:
        record = session.query(CompanyPublicData).filter(CompanyPublicData.siren == row["siren"]).first()
        if record is None:
            record = CompanyPublicData(siren=row["siren"])
            session.add(record)
            inserted += 1
        else:
            updated += 1
        for field in TABLE_FIELDS:
            setattr(record, field, row.get(field))
        record.collected_at = datetime.now(timezone.utc)
    session.flush()
    logger.info("Load: %s inserted, %s updated in company_public_data", inserted, updated)
    return {"inserted": inserted, "updated": updated}
