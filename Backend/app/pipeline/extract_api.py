"""Source 3 - REST API: the official "API Recherche d'entreprises" (data.gouv.fr, no API key).

One GET per SIREN, with retries on temporary errors and a delay that keeps us under the
API rate limit. The list of company officers ("dirigeants") is personal data and is never kept.
"""
import logging
import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.pipeline import config

logger = logging.getLogger("pipeline.api")


def build_session() -> requests.Session:
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1.0, status_forcelist=[429, 500, 502, 503, 504],
                    allowed_methods=["GET"], respect_retry_after_header=True)
    session.mount("https://", HTTPAdapter(max_retries=retries))
    session.headers.update({"User-Agent": config.USER_AGENT, "Accept": "application/json"})
    return session


def parse_api_result(result: dict) -> dict:
    """Keep only the fields the project needs, flattened."""
    head_office = result.get("siege") or {}
    return {
        "siren": result.get("siren"),
        "legal_name": result.get("nom_raison_sociale") or result.get("nom_complet"),
        "legal_form_code": result.get("nature_juridique"),
        "naf_code": result.get("activite_principale") or head_office.get("activite_principale"),
        "naf_section": result.get("section_activite_principale"),
        "headcount_code": result.get("tranche_effectif_salarie"),
        "company_category": result.get("categorie_entreprise"),
        "creation_date": result.get("date_creation") or head_office.get("date_creation"),
        "administrative_state": result.get("etat_administratif"),
        "head_office_address": head_office.get("adresse"),
        "postal_code": head_office.get("code_postal"),
        "city": head_office.get("libelle_commune"),
    }


def fetch_company(session: requests.Session, siren: str) -> dict | None:
    response = session.get(config.API_URL, params={"q": siren, "per_page": 5},
                           timeout=config.HTTP_TIMEOUT_SECONDS)
    response.raise_for_status()
    for result in response.json().get("results", []):
        if result.get("siren") == siren:  # the search is full-text: keep the exact match only
            return parse_api_result(result)
    return None


def extract_api(sirens: list[str], session: requests.Session | None = None) -> tuple[dict, list[dict]]:
    """Return ({siren: record}, [errors]). One failing SIREN never stops the others."""
    session = session or build_session()
    records, errors = {}, []
    for index, siren in enumerate(sirens):
        if index:
            time.sleep(config.API_DELAY_SECONDS)
        try:
            record = fetch_company(session, siren)
        except (requests.RequestException, ValueError) as error:
            logger.warning("API: SIREN %s failed: %s", siren, error)
            errors.append({"source": "api", "siren": siren, "reason": f"{type(error).__name__}: {error}"})
            continue
        if record is None:
            logger.info("API: SIREN %s not found", siren)
            continue
        records[siren] = record
    logger.info("API source: %s/%s SIRENs found", len(records), len(sirens))
    return records, errors
