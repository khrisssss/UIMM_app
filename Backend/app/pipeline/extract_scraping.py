"""Source 4 - scraping: a short description of each company, read from its public homepage.

Polite by design: robots.txt is checked first, one page per site, a delay between sites,
an identified User-Agent, a size limit, and only the <title> and meta description are kept.
"""
import logging
import time
from urllib import robotparser
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from app.pipeline import config

logger = logging.getLogger("pipeline.scraping")


def extract_description(html: str) -> str | None:
    """Return the meta description (or Open Graph description), else the page title."""
    soup = BeautifulSoup(html, "html.parser")
    for attributes in ({"name": "description"}, {"property": "og:description"}):
        tag = soup.find("meta", attrs=attributes)
        if tag and tag.get("content", "").strip():
            return tag["content"].strip()
    if soup.title and soup.title.string and soup.title.string.strip():
        return soup.title.string.strip()
    return None


def robots_allows(session: requests.Session, url: str) -> bool:
    parts = urlparse(url)
    robots_url = f"{parts.scheme}://{parts.netloc}/robots.txt"
    response = session.get(robots_url, timeout=config.HTTP_TIMEOUT_SECONDS)
    if response.status_code == 404:
        return True  # no robots.txt: no restriction declared
    if response.status_code >= 400:
        return False  # robots.txt unreadable: do not scrape
    parser = robotparser.RobotFileParser()
    parser.parse(response.text.splitlines())
    return parser.can_fetch(config.USER_AGENT, url)


def scrape_homepage(session: requests.Session, url: str) -> dict:
    if not robots_allows(session, url):
        return {"status": "blocked_by_robots_txt", "website_description": None}
    with session.get(url, timeout=config.HTTP_TIMEOUT_SECONDS, stream=True) as response:
        response.raise_for_status()
        if "text/html" not in response.headers.get("Content-Type", ""):
            return {"status": "not_html", "website_description": None}
        content = b""
        for chunk in response.iter_content(chunk_size=65536):
            content += chunk
            if len(content) > config.MAX_PAGE_BYTES:
                break
        html = content.decode(response.encoding or "utf-8", errors="replace")
    return {"status": "ok", "website_description": extract_description(html)}


def extract_scraping(websites: dict[str, str], session: requests.Session | None = None) -> tuple[dict, list[dict]]:
    """websites = {siren: url}. Return ({siren: {website_description, status}}, [errors])."""
    session = session or requests.Session()
    session.headers.update({"User-Agent": config.USER_AGENT})
    records, errors = {}, []
    for index, (siren, url) in enumerate(websites.items()):
        if index:
            time.sleep(config.SCRAPING_DELAY_SECONDS)
        try:
            result = scrape_homepage(session, url)
        except requests.RequestException as error:
            logger.warning("Scraping: %s failed: %s", url, error)
            errors.append({"source": "scraping", "siren": siren, "reason": f"{type(error).__name__}: {error}"})
            continue
        if result["status"] != "ok":
            logger.info("Scraping: %s skipped (%s)", url, result["status"])
        records[siren] = result
    scraped = sum(1 for record in records.values() if record["website_description"])
    logger.info("Scraping source: %s/%s descriptions collected", scraped, len(websites))
    return records, errors
