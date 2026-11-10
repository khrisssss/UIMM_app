import os
from pathlib import Path
import subprocess
import sys

import pytest
from app.models.answer import Answer
from app.models.company import Company
from app.models.company_axis import CompanyAxis
from app.models.company_profile_answer import CompanyProfileAnswer
from app.models.score import Score
from app.services.public_company_import_service import import_public_companies, load_public_companies, normalize


def test_public_catalog_has_twenty_distinct_sourced_company_profiles():
    records = load_public_companies()
    assert len(records) == len({normalize(r['name']) for r in records}) == 20
    assert all(r['source_urls'] and r['address'] and r['activity'] for r in records)
    assert all(r['verified_on'] == '2026-10-26' for r in records)
    assert not any('demo' in r['name'].lower() for r in records)


def test_public_import_preview_writes_nothing(configured_db):
    result = import_public_companies(configured_db)
    assert result['companies_added'] == 20 and not result['apply']
    assert configured_db.query(Company).count() == 0
    assert configured_db.query(CompanyProfileAnswer).count() == 0
    assert not configured_db.new


def test_public_import_creates_profiles_and_six_axes_without_assessments(configured_db):
    db = configured_db
    result = import_public_companies(db, apply=True); db.commit()
    assert result['companies_added'] == db.query(Company).count() == 20
    assert db.query(CompanyAxis).count() == 20 * 6
    assert db.query(CompanyProfileAnswer).count() == 20
    assert db.query(Answer).count() == db.query(Score).count() == 0
    assert all(c.general_state == 'unassessed' and not c.is_archived and c.company_size is None for c in db.query(Company))
    assert all('Sources consultées' in a.answer_text and 'https://' in a.answer_text for a in db.query(CompanyProfileAnswer))
    repeated = import_public_companies(db, apply=True)
    assert repeated['companies_added'] == 0 and repeated['companies_kept'] == 20
    assert db.query(CompanyProfileAnswer).count() == 20


def test_existing_company_and_its_manual_fields_are_preserved(configured_db):
    company = Company(name='Latécoère', general_comment='Consultant notes', contact_name='Existing contact', general_state='red', is_archived=True)
    configured_db.add(company); configured_db.commit()
    result = import_public_companies(configured_db, apply=True)
    assert result['companies_added'] == 19 and result['companies_kept'] == 1
    assert company.general_comment == 'Consultant notes' and company.contact_name == 'Existing contact'
    assert company.general_state == 'red' and company.is_archived
    assert configured_db.query(CompanyProfileAnswer).filter_by(company_id=company.id).count() == 0


def test_ambiguous_existing_names_stop_import_before_any_write(configured_db):
    configured_db.add_all([Company(name='Latecoere'), Company(name='Latécoère')]); configured_db.commit()
    with pytest.raises(ValueError, match='Ambiguous existing company'):
        import_public_companies(configured_db, apply=True)
    assert configured_db.query(Company).count() == 2
    assert configured_db.query(CompanyProfileAnswer).count() == 0


def test_public_import_requires_sources_and_rolls_back(configured_db):
    record = load_public_companies()[0]
    with pytest.raises(ValueError, match='sources'):
        import_public_companies(configured_db, apply=True, records=[{**record, 'source_urls': []}])
    configured_db.rollback()
    with pytest.raises(RuntimeError):
        with configured_db.begin():
            import_public_companies(configured_db, apply=True, records=[record])
            raise RuntimeError('Simulated failure')
    assert configured_db.query(Company).count() == 0


def test_standalone_import_resolves_models_in_fresh_process():
    code = 'from app.scripts.import_toulouse_companies import main; from sqlalchemy.orm import configure_mappers; configure_mappers()'
    result = subprocess.run([sys.executable, '-c', code], cwd=Path(__file__).resolve().parents[1], env={**os.environ, 'DATABASE_URL': 'sqlite://'}, text=True, capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr
