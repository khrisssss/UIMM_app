import os
from pathlib import Path
import subprocess
import sys

import pytest
from app.models.answer import Answer
from app.models.company import Company
from app.models.score import Score
from app.models.swot import SWOT
from app.services.public_company_import_service import import_public_companies
from app.services.public_swot_service import create_public_swot, plan_public_swots
from app.services.swot_ai_payload import make_swot_ai_payload
from app.services.swot_generation_service import normalize_ai_swot


def test_payload_excludes_unanswered_axis_scores_preserves_answered_zero():
    context = {'company': {'has_rse': False}, 'company_profile': [{'question': 'Présentation — recherche documentaire publique', 'answer': 'Conception et fabrication de pièces.'}], 'axis_scores': [
        {'axis_name': 'RH', 'percentage': 0, 'answered_questions': 0},
    ]}
    payload = make_swot_ai_payload(context, ())
    assert payload['evidence_basis']['mode'] == 'public_sources_only'
    assert payload['company_context']['has_rse'] is None
    assert payload['axis_scores'] == []
    context['axis_scores'].append({'axis_name': 'Stratégie', 'percentage': 0, 'answered_questions': 2})
    context['diagnostic_answers'] = [{'axis_name': 'Stratégie', 'score_value': 0, 'max_score': 5, 'suggested_swot_type': 'weakness'}]
    diagnostic = make_swot_ai_payload(context, ())
    assert diagnostic['evidence_basis']['mode'] == 'diagnostic'
    assert [s['axis'] for s in diagnostic['axis_scores']] == ['Stratégie']
    assert diagnostic['axis_scores'][0]['percentage'] == 0


def test_batch_previews_twenty_and_saves_drafts_without_answers_or_scores(configured_db):
    db = configured_db
    import_public_companies(db, apply=True); db.commit()
    plan = plan_public_swots(db)
    assert len(plan['eligible']) == 20
    assert not plan['skipped']
    assert db.query(SWOT).count() == 0
    calls = []
    def generator(payload):
        assert payload['axis_scores'] == payload['answer_scores'] == []
        assert payload['evidence_basis']['mode'] == 'public_sources_only'
        assert payload['company_profile']
        calls.append(payload)
        return {'strengths': ['Selon les informations publiques : capacité industrielle déclarée.'], 'weaknesses': [], 'opportunities': [], 'threats': []}
    for item in plan['eligible']:
        result = create_public_swot(db, item['company_id'], generator=generator)
        assert result.status == 'draft' and result.generation_source == 'public_sources_ai'
        assert isinstance(result.strengths, str) and result.weaknesses == ''
    db.commit()
    assert len(calls) == db.query(SWOT).count() == 20
    assert db.query(Answer).count() == db.query(Score).count() == 0
    assert all(c.general_state == 'unassessed' for c in db.query(Company))
    assert not plan_public_swots(db)['eligible']
    assert len(plan_public_swots(db)['skipped']) == 20


def test_batch_preserves_existing_manual_swot(configured_db):
    db = configured_db
    import_public_companies(db, apply=True); db.commit()
    company = db.query(Company).first()
    existing = SWOT(company_id=company.id, strengths='Consultant finding', status='validated', generation_source='manual')
    db.add(existing); db.commit()
    with pytest.raises(ValueError, match='existing_swot_preserved'):
        create_public_swot(db, company.id, generator=lambda _: {})
    assert existing.strengths == 'Consultant finding' and existing.status == 'validated'


def test_ai_failure_does_not_save_or_create_diagnostic_data(configured_db):
    db = configured_db
    import_public_companies(db, apply=True); db.commit()
    company_id = db.query(Company.id).first()[0]
    db.rollback()
    with pytest.raises(ValueError, match='list of text'):
        with db.begin():
            create_public_swot(db, company_id, generator=lambda _: {'strengths': {'not': 'a list'}})
    assert db.query(SWOT).count() == db.query(Score).count() == 0


def test_swot_text_storage_and_empty_sections():
    assert normalize_ai_swot({'strengths': [' A ', '', 'B']}) == {'strengths': 'A\nB', 'weaknesses': '', 'opportunities': '', 'threats': ''}
    with pytest.raises(ValueError):
        normalize_ai_swot(None)


def test_standalone_batch_import_needs_no_api_credentials_or_preloaded_models():
    result = subprocess.run([sys.executable, '-c', 'from app.scripts.generate_public_company_swots import main; from sqlalchemy.orm import configure_mappers; configure_mappers()'], cwd=Path(__file__).resolve().parents[1], env={**os.environ, 'DATABASE_URL': 'sqlite://'}, text=True, capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr
