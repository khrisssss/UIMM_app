"""Settings of the public-data pipeline. Every value can be overridden by an environment variable."""
import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.getenv("PIPELINE_DATA_DIR", BACKEND_DIR / "pipeline_data"))
RAW_DIR = DATA_DIR / "raw"
OUTPUT_DIR = DATA_DIR / "output"
LOG_DIR = DATA_DIR / "logs"

# Source 3 - REST API: official "API Recherche d'entreprises" (no key, about 7 requests/second allowed)
API_URL = os.getenv("COMPANY_API_URL", "https://recherche-entreprises.api.gouv.fr/search")
API_DELAY_SECONDS = float(os.getenv("COMPANY_API_DELAY", "0.2"))  # 5 requests/second at most

# Source 5 - big data: INSEE SIRENE stock of legal units (Parquet, ~29 million rows, ~680 MB, monthly)
SIRENE_PARQUET_URL = os.getenv(
    "SIRENE_PARQUET_URL",
    "https://www.data.gouv.fr/api/1/datasets/r/350182c9-148a-46e0-8389-76c2ec1374a3",
)
SIRENE_LOCAL_FILE = RAW_DIR / "StockUniteLegale.parquet"

# Source 4 - scraping: company websites, read politely
SCRAPING_DELAY_SECONDS = float(os.getenv("SCRAPING_DELAY", "1.0"))
MAX_PAGE_BYTES = 2_000_000

HTTP_TIMEOUT_SECONDS = 15
USER_AGENT = "UIMM-Boost-data-pipeline/1.0 (UIMM Occitanie internal tool)"

# INSEE headcount brackets ("tranche d'effectif salarié")
HEADCOUNT_LABELS = {
    "NN": "Non employeur ou effectif inconnu",
    "00": "0 salarié",
    "01": "1 ou 2 salariés",
    "02": "3 à 5 salariés",
    "03": "6 à 9 salariés",
    "11": "10 à 19 salariés",
    "12": "20 à 49 salariés",
    "21": "50 à 99 salariés",
    "22": "100 à 199 salariés",
    "31": "200 à 249 salariés",
    "32": "250 à 499 salariés",
    "41": "500 à 999 salariés",
    "42": "1 000 à 1 999 salariés",
    "51": "2 000 à 4 999 salariés",
    "52": "5 000 à 9 999 salariés",
    "53": "10 000 salariés et plus",
}
