"""Tests for the public-data pipeline. No network access: the API and websites are faked,
and the big-data test builds a small Parquet file with the real SIRENE column names."""
from datetime import date
from types import SimpleNamespace

import duckdb
import pytest
import requests
from fastapi import HTTPException
from sqlalchemy.orm import sessionmaker

from app.models.axis import Axis
from app.models.company import Company
from app.models.company_public_data import CompanyPublicData
from app.models.score import Score
from app.pipeline import aggregate as agg
from app.pipeline import extract_api, extract_bigdata, extract_scraping
from app.pipeline.extract_database import extract_database
from app.pipeline.extract_file import extract_file
from app.pipeline.load import load
from app.routers.public_data import read_company_public_data
from app.schemas.company import CompanyCreate
from app.services.siren import normalize_siren


# ---------- SIREN ----------

def test_siren_is_cleaned_and_checked():
    assert normalize_siren("552 032 534") == "552032534"
    assert normalize_siren("") is None
    with pytest.raises(ValueError):
        normalize_siren("12345678")      # 8 digits
    with pytest.raises(ValueError):
        normalize_siren("123456789")     # wrong checksum


def test_company_form_rejects_invalid_siren():
    assert CompanyCreate(name="Test", siren="552 032 534").siren == "552032534"
    with pytest.raises(ValueError):
        CompanyCreate(name="Test", siren="123456789")


# ---------- Source 1: file ----------

def test_file_source_reads_semicolon_csv(tmp_path):
    path = tmp_path / "companies.csv"
    path.write_text("SIREN;Name;Website\n552032534;Danone;danone.com\n;Empty;\n", encoding="utf-8")
    rows = extract_file(path)
    assert rows[0] == {"line": 2, "siren": "552032534", "name": "Danone", "website": "danone.com"}
    assert rows[1]["siren"] == ""


def test_file_source_requires_a_siren_column(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("name\nDanone\n", encoding="utf-8")
    with pytest.raises(ValueError):
        extract_file(path)


# ---------- Source 2: database (SQL) ----------

def test_database_source_selects_real_companies_with_their_average_score(db):
    active, retired = Axis(name="Stratégie", order_index=1, is_active=True), Axis(name="Finance", order_index=2, is_active=False)
    real = Company(name="Real", siren="552032534")
    db.add_all([active, retired, real,
                Company(name="No SIREN"),
                Company(name="Archived", siren="552081317", is_archived=True),
                Company(name="Demo", siren="542051180", is_synthetic=True)])
    db.flush()
    db.add_all([Score(company_id=real.id, axis_id=active.id, score_percentage=60.0),
                Score(company_id=real.id, axis_id=retired.id, score_percentage=0.0)])
    db.flush()

    rows = extract_database(db)

    assert len(rows) == 1
    assert rows[0]["siren"] == "552032534"
    assert rows[0]["scored_axes"] == 1                 # the retired axis is ignored
    assert rows[0]["avg_score_percentage"] == 60.0


# ---------- Source 3: REST API ----------

class FakeResponse:
    def __init__(self, payload=None, status=200, text="", headers=None):
        self.payload, self.status_code, self.text = payload, status, text
        self.headers = headers or {}

    def json(self):
        return self.payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


API_RESULT = {
    "siren": "552032534", "nom_complet": "DANONE", "nom_raison_sociale": "DANONE", "nature_juridique": "5599",
    "activite_principale": "70.10Z", "section_activite_principale": "M", "tranche_effectif_salarie": "21",
    "categorie_entreprise": "GE", "date_creation": "1955-01-01", "etat_administratif": "A",
    "siege": {"adresse": "17 BOULEVARD HAUSSMANN 75009 PARIS", "code_postal": "75009", "libelle_commune": "PARIS"},
    "dirigeants": [{"nom": "PERSON", "prenoms": "PRIVATE"}],
}


def test_api_source_keeps_exact_match_and_drops_personal_data(monkeypatch):
    monkeypatch.setattr(extract_api.config, "API_DELAY_SECONDS", 0)
    other = dict(API_RESULT, siren="999999999")
    session = SimpleNamespace(get=lambda url, params, timeout: FakeResponse({"results": [other, API_RESULT]}))

    records, errors = extract_api.extract_api(["552032534"], session=session)

    record = records["552032534"]
    assert record["naf_code"] == "70.10Z" and record["city"] == "PARIS"
    assert "dirigeants" not in record and errors == []


def test_api_source_continues_after_an_error(monkeypatch):
    monkeypatch.setattr(extract_api.config, "API_DELAY_SECONDS", 0)

    def get(url, params, timeout):
        if params["q"] == "552081317":
            raise requests.ConnectionError("network down")
        return FakeResponse({"results": [API_RESULT]})

    records, errors = extract_api.extract_api(["552081317", "552032534"], session=SimpleNamespace(get=get))

    assert list(records) == ["552032534"]
    assert errors[0]["siren"] == "552081317"


# ---------- Source 4: scraping ----------

def test_description_comes_from_meta_then_title():
    assert extract_scraping.extract_description('<meta name="description" content=" Fabricant de pièces ">') == "Fabricant de pièces"
    assert extract_scraping.extract_description("<html><title>Atelier Dupont</title></html>") == "Atelier Dupont"
    assert extract_scraping.extract_description("<html></html>") is None


def test_scraping_respects_robots_txt(monkeypatch):
    monkeypatch.setattr(extract_scraping.config, "SCRAPING_DELAY_SECONDS", 0)
    calls = []

    def get(url, timeout, **kwargs):
        calls.append(url)
        return FakeResponse(status=200, text="User-agent: *\nDisallow: /\n")

    records, errors = extract_scraping.extract_scraping({"552032534": "https://example.com/"},
                                                        session=SimpleNamespace(get=get, headers={}))

    assert records["552032534"]["status"] == "blocked_by_robots_txt"
    assert calls == ["https://example.com/robots.txt"]  # the homepage itself was never requested


# ---------- Source 5: big data (DuckDB on Parquet) ----------

@pytest.fixture
def sirene_parquet(tmp_path):
    path = tmp_path / "StockUniteLegale.parquet"
    connection = duckdb.connect()
    connection.execute("""
        CREATE TABLE stock AS SELECT * FROM (VALUES
            ('552032534', 'DANONE', '5599', '70.10Z', '21', 'GE', DATE '1955-01-01', 'A'),
            ('111111118', 'ATELIER A', '5499', '25.62B', '11', 'PME', DATE '2001-03-01', 'A'),
            ('222222226', 'ATELIER B', '5499', '25.62B', '02', 'PME', DATE '1990-05-12', 'C'),
            ('333333334', 'ATELIER C', '5499', '25.62B', '12', 'PME', DATE '2015-09-30', 'A')
        ) AS t(siren, denominationUniteLegale, categorieJuridiqueUniteLegale, activitePrincipaleUniteLegale,
               trancheEffectifsUniteLegale, categorieEntreprise, dateCreationUniteLegale, etatAdministratifUniteLegale)
    """)
    connection.execute(f"COPY stock TO '{path}' (FORMAT PARQUET)")
    connection.close()
    return path


def test_bigdata_lookup_and_sector_size(sirene_parquet):
    records, connection = extract_bigdata.extract_bigdata(["111111118", "000000000"], sirene_parquet)
    counts = extract_bigdata.count_active_by_naf(connection, {"25.62B"})
    connection.close()

    assert list(records) == ["111111118"]
    assert records["111111118"]["naf_code"] == "25.62B"
    assert counts == {"25.62B": 2}  # the closed company ('C') is not counted


def test_bigdata_refuses_the_wrong_file(tmp_path):
    path = tmp_path / "other.parquet"
    duckdb.connect().execute(f"COPY (SELECT 1 AS siren) TO '{path}' (FORMAT PARQUET)")
    with pytest.raises(ValueError, match="StockUniteLegale"):
        extract_bigdata.open_sirene(path)


# ---------- Aggregation and cleaning ----------

def test_aggregation_cleans_merges_and_rejects():
    file_rows = [
        {"line": 2, "siren": "552 032 534", "name": " Danone ", "website": "WWW.Danone.com"},
        {"line": 3, "siren": "552032534", "name": "Danone again", "website": ""},
        {"line": 4, "siren": "12345678", "name": "Typo", "website": ""},
        {"line": 5, "siren": "111111118", "name": "Sole trader", "website": ""},
        {"line": 6, "siren": "552081317", "name": "Unknown", "website": ""},
        {"line": 7, "siren": "333333334", "name": "Partial diffusion", "website": ""},
    ]
    api = {"552032534": {"legal_name": "DANONE", "naf_code": "7010z", "headcount_code": "21",
                         "administrative_state": "A", "creation_date": "1955-01-01", "legal_form_code": "5599",
                         "head_office_address": "17  BOULEVARD   HAUSSMANN", "city": "PARIS"}}
    sirene = {
        "552032534": {"legal_name": "OLD NAME", "naf_code": "70.10Z", "company_category": "GE"},
        "111111118": {"legal_name": "JEAN DUPONT", "legal_form_code": "1000", "naf_code": "25.62B",
                      "headcount_code": "0", "administrative_state": "A", "creation_date": date(2001, 3, 1)},
        "333333334": {"legal_name": "OPPOSED", "legal_form_code": "5499", "diffusion_status": "P"},
    }

    dataset, rejected = agg.aggregate(file_rows, [], api, sirene, {"70.10Z": 1500}, {"552032534": {"website_description": "Food"}})

    danone = next(row for row in dataset if row["siren"] == "552032534")
    assert danone["legal_name"] == "DANONE"                       # API wins over the monthly stock
    assert danone["company_category"] == "GE"                     # stock fills the gap
    assert danone["naf_code"] == "70.10Z" and danone["naf_section"] == "M"
    assert danone["creation_date"] == date(1955, 1, 1) and danone["is_active"] is True
    assert danone["headcount_label"] == "50 à 99 salariés"
    assert danone["head_office_address"] == "17 BOULEVARD HAUSSMANN"
    assert danone["website"] == "https://www.danone.com/"
    assert danone["sector_active_companies"] == 1500
    assert danone["sources"] == "file,api,sirene,scraping"

    trader = next(row for row in dataset if row["siren"] == "111111118")
    assert trader["legal_name"] is None and trader["head_office_address"] is None  # RGPD: a person's name
    assert trader["headcount_code"] == "00"
    assert next(row for row in dataset if row["siren"] == "333333334")["legal_name"] is None  # opposition (status P)

    reasons = {row["line"]: row["reason"] for row in rejected}
    assert "Duplicate" in reasons[3] and "9 digits" in reasons[4] and "not found" in reasons[6]


# ---------- Load into PostgreSQL (upsert) and API route ----------

def test_load_inserts_then_updates_without_duplicates(db):
    row = {"siren": "552032534", "legal_name": "DANONE", "naf_code": "70.10Z", "is_active": True, "sources": "api"}
    assert load(db, [row]) == {"inserted": 1, "updated": 0}
    assert load(db, [dict(row, naf_code="10.51A")]) == {"inserted": 0, "updated": 1}
    assert db.query(CompanyPublicData).count() == 1
    assert db.query(CompanyPublicData).one().naf_code == "10.51A"


def test_route_returns_public_data_through_the_company_siren(db):
    company = Company(name="Danone", siren="552032534")
    no_siren = Company(name="Other")
    db.add_all([company, no_siren])
    load(db, [{"siren": "552032534", "legal_name": "DANONE", "sources": "api"}])

    assert read_company_public_data(company.id, db=db, current_user=None).legal_name == "DANONE"
    with pytest.raises(HTTPException) as error:
        read_company_public_data(no_siren.id, db=db, current_user=None)
    assert error.value.status_code == 404


# ---------- Full run, offline ----------

def test_full_run_end_to_end(db, tmp_path, sirene_parquet, monkeypatch):
    from app import database
    from app.pipeline import run as pipeline_run

    db.add(Company(name="Atelier C", siren="333333334"))
    db.commit()
    monkeypatch.setattr(database, "SessionLocal", sessionmaker(bind=db.get_bind()))
    monkeypatch.setattr(pipeline_run, "extract_api", lambda sirens: ({"552032534": extract_api.parse_api_result(API_RESULT)}, []))
    monkeypatch.setattr(pipeline_run, "extract_scraping", lambda websites: ({}, []))
    input_file = tmp_path / "companies.csv"
    input_file.write_text("siren,name,website\n552032534,Danone,danone.com\n123456789,Bad,\n", encoding="utf-8")

    summary = pipeline_run.run(input_file, sirene_file=sirene_parquet, output_dir=tmp_path / "out")

    assert summary["dataset_rows"] == 2          # Danone from the file + Atelier C from the database
    assert summary["rejected_rows"] == 1
    assert summary["load"] == {"inserted": 2, "updated": 0}
    assert (tmp_path / "out" / "company_public_dataset.csv").exists()
    atelier = db.query(CompanyPublicData).filter_by(siren="333333334").one()
    assert atelier.sector_active_companies == 2 and atelier.sources == "database,sirene"


# ---------- Regression: the SIREN typed in the app is saved ----------

def test_company_creation_saves_the_siren(db):
    from app.routers.companies import create_company

    company = create_company(CompanyCreate(name="Danone", siren="552 032 534"), db=db, current_user=None)

    assert company.siren == "552032534"


def test_bigdata_reads_the_diffusion_status_when_present(tmp_path):
    path = tmp_path / "with_status.parquet"
    duckdb.connect().execute(f"""COPY (SELECT * FROM (VALUES
        ('552032534', 'X', '5599', '70.10Z', '21', 'GE', DATE '1955-01-01', 'A', 'P')
    ) AS t(siren, denominationUniteLegale, categorieJuridiqueUniteLegale, activitePrincipaleUniteLegale,
           trancheEffectifsUniteLegale, categorieEntreprise, dateCreationUniteLegale, etatAdministratifUniteLegale,
           statutDiffusionUniteLegale)) TO '{path}' (FORMAT PARQUET)""")
    connection = extract_bigdata.open_sirene(path)

    assert extract_bigdata.lookup_companies(connection, ["552032534"])["552032534"]["diffusion_status"] == "P"


# ---------- Live search used by the company creation form ----------

def test_search_maps_headcount_to_the_app_sizes():
    from app.routers.public_data import suggested_company_size

    assert [suggested_company_size(code) for code in ["00", "03", "11", "12", "21", "53", "NN", None]] == \
        ["<10", "<10", "11-50", "11-50", ">50", ">50", None, None]


def test_search_by_siren_keeps_the_exact_company(monkeypatch):
    from app.routers import public_data

    other = extract_api.parse_api_result(dict(API_RESULT, siren="552081317", nom_raison_sociale="OTHER"))
    monkeypatch.setattr(public_data, "search_companies", lambda session, query: [other, extract_api.parse_api_result(API_RESULT)])

    results = public_data.search_public_companies(q="552 032 534", current_user=None)

    assert [r.siren for r in results] == ["552032534"]
    found = results[0]
    assert found.legal_name == "DANONE" and found.suggested_company_size == ">50"
    assert found.head_office_address.startswith("17 BOULEVARD HAUSSMANN") and found.is_active is True


def test_search_reports_an_unavailable_service(monkeypatch):
    from app.routers import public_data

    def down(session, query):
        raise requests.ConnectionError("down")

    monkeypatch.setattr(public_data, "search_companies", down)
    with pytest.raises(HTTPException) as error:
        public_data.search_public_companies(q="danone", current_user=None)
    assert error.value.status_code == 502

    with pytest.raises(HTTPException) as error:
        public_data.search_public_companies(q="123456789", current_user=None)  # wrong checksum
    assert error.value.status_code == 422
