"""Generate reviewable SWOT drafts from imported public profiles, without scores."""
import os
from app.models.company import Company
from app.models.axis_question_category import AxisQuestionCategory  # noqa: F401 -- standalone ORM target
from app.models.company_profile_answer import CompanyProfileAnswer
from app.models.company_profile_question import CompanyProfileQuestion
from app.models.swot import SWOT
from app.services.public_company_import_service import PROFILE_QUESTION, load_public_companies, normalize
from app.services.swot_context import build_swot_context
from app.services.swot_ai_payload import make_swot_ai_payload
from app.services.swot_generation_service import normalize_ai_swot


def public_draft_input(db, company_id):
    company = db.query(Company).filter_by(id=company_id).first()
    if company is None:
        return None, 'company_not_found'
    if db.query(SWOT).filter_by(company_id=company_id, axis_id=None).first():
        return None, 'existing_swot_preserved'
    if company.general_state != 'unassessed':
        return None, 'company_already_assessed'
    public_answer = db.query(CompanyProfileAnswer).join(CompanyProfileQuestion).filter(
        CompanyProfileAnswer.company_id == company_id,
        CompanyProfileQuestion.question_text == PROFILE_QUESTION,
        CompanyProfileAnswer.answer_text.isnot(None),
    ).first()
    if public_answer is None or not public_answer.answer_text.strip():
        return None, 'public_profile_missing'
    payload = make_swot_ai_payload(build_swot_context(db, company_id), ())
    if payload['evidence_basis']['mode'] != 'public_sources_only':
        return None, 'diagnostic_evidence_present'
    return payload, None


def plan_public_swots(db):
    catalog_names = {normalize(name) for record in load_public_companies() for name in [record['name'], *record.get('aliases', [])]}
    companies = db.query(Company).order_by(Company.id).all()
    eligible, skipped = [], []
    for company in companies:
        if normalize(company.name) not in catalog_names:
            continue
        _, reason = public_draft_input(db, company.id)
        item = {'company_id': company.id, 'name': company.name}
        if reason:
            skipped.append({**item, 'reason': reason})
        else:
            eligible.append(item)
    return {'eligible': eligible, 'skipped': skipped}


def create_public_swot(db, company_id, *, generator=None):
    """One company per caller-owned transaction; never replace an existing SWOT."""
    payload, reason = public_draft_input(db, company_id)
    if reason:
        raise ValueError(reason)
    if generator is None:
        from app.services.swot_ai_service import generate_swot_with_ai
        generator = generate_swot_with_ai
    findings = normalize_ai_swot(generator(payload))
    record = SWOT(company_id=company_id, axis_id=None, **findings, generation_source='public_sources_ai', generated_by_ai=True, ai_model=os.getenv('AZURE_OPENAI_MODEL', 'azure-model'), status='draft')
    db.add(record)
    db.flush()
    return record
