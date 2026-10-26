"""Import sourced public company profiles without inventing diagnostic responses."""
import json
import unicodedata
from pathlib import Path
from urllib.parse import urlparse

from app.models.axis import Axis
from app.models.company import Company
from app.models.company_axis import CompanyAxis
from app.models.company_profile_section import CompanyProfileSection
from app.models.company_profile_question import CompanyProfileQuestion
from app.models.company_profile_answer import CompanyProfileAnswer

DATA_PATH = Path(__file__).resolve().parents[1] / 'data' / 'toulouse_companies_public.json'
PROFILE_QUESTION = 'Présentation de l’entreprise — recherche documentaire publique'
SIX_AXES = ['Stratégie', 'Performance', 'Marketing', 'RH', 'Digitalisation', 'RSE']


def normalize(value):
    value = unicodedata.normalize('NFKD', value.casefold())
    return ' '.join(''.join(c if c.isalnum() else ' ' for c in value if not unicodedata.combining(c)).split())


def load_public_companies():
    return json.loads(DATA_PATH.read_text(encoding='utf-8'))['companies']


def validate_records(records):
    identities = set()
    for record in records:
        if any(not record.get(field) for field in ['name', 'city', 'address', 'activity', 'source_urls', 'verified_on']):
            raise ValueError('Each public profile needs its name, location, activity, sources and verification date')
        for url in record['source_urls']:
            if urlparse(url).scheme != 'https' or not urlparse(url).netloc:
                raise ValueError('Each source must be an HTTPS URL')
        record_identities = {normalize(name) for name in [record['name'], *record.get('aliases', [])]}
        if '' in record_identities or identities.intersection(record_identities):
            raise ValueError(f"Duplicate or empty public company identity: {record['name']}")
        identities.update(record_identities)


def profile_text(record):
    return (
        f"Activité publiée : {record['activity']}\n"
        f"Implantation : {record['address']}\n"
        f"Sources consultées le {record['verified_on']} :\n" + '\n'.join(record['source_urls']) +
        '\nFiche documentaire publique. Aucun entretien ou diagnostic réalisé ; réponses internes et scores à compléter après validation.'
    )


def import_public_companies(db, *, apply=False, records=None):
    """Preview by default. Caller owns the transaction; existing companies are kept."""
    records = load_public_companies() if records is None else records
    validate_records(records)
    axes = db.query(Axis).filter_by(is_active=True).all()
    axes_by_name = {normalize(a.name): a for a in axes}
    if any(normalize(name) not in axes_by_name for name in SIX_AXES):
        raise ValueError('Configure the six active diagnostic axes before importing public profiles')
    selected_axes = [axes_by_name[normalize(name)] for name in SIX_AXES]
    existing_by_name = {}
    for company in db.query(Company).all():
        existing_by_name.setdefault(normalize(company.name), []).append(company)
    planned = []
    kept = []
    for record in records:
        matches = {c.id: c for name in [record['name'], *record.get('aliases', [])] for c in existing_by_name.get(normalize(name), [])}
        if len(matches) > 1:
            raise ValueError(f"Ambiguous existing company: {record['name']}. Review duplicates before import.")
        if matches:
            kept.append(record['name'])
        else:
            planned.append(record)
    summary = {'companies_added': len(planned), 'companies_kept': len(kept), 'apply': apply, 'dataset_kind': 'public_company_profiles', 'diagnostic_answers_created': 0, 'scores_created': 0, 'new_companies': [r['name'] for r in planned], 'existing_companies': kept}
    if not apply or not planned:
        return summary
    sections = [s for s in db.query(CompanyProfileSection).all() if normalize(s.name) == normalize('Informations Générales')]
    if len(sections) > 1:
        raise ValueError('Ambiguous Informations Générales sections')
    section = sections[0] if sections else None
    if section is None:
        maximum = max((s.order_index for s in db.query(CompanyProfileSection).all()), default=0)
        section = CompanyProfileSection(name='Informations Générales', order_index=maximum + 1, is_active=True)
        db.add(section); db.flush()
    if not section.is_active:
        raise ValueError('Informations Générales is inactive; review the section before import')
    questions = db.query(CompanyProfileQuestion).filter_by(section_id=section.id).all()
    matching = [q for q in questions if normalize(q.question_text) == normalize(PROFILE_QUESTION)]
    if len(matching) > 1:
        raise ValueError('Ambiguous public profile question')
    question = matching[0] if matching else None
    if question is None:
        question = CompanyProfileQuestion(section_id=section.id, question_text=PROFILE_QUESTION, order_index=max((q.order_index for q in questions), default=0) + 1, is_active=True)
        db.add(question); db.flush()
    if not question.is_active:
        raise ValueError('Public profile question is inactive; review it before import')
    for record in planned:
        text = profile_text(record)
        company = Company(name=record['name'], address=record['address'], status='Prospect', is_archived=False, general_state='unassessed', company_size=None, general_comment=text + '\nTaille, démarche RSE et autres informations internes : à confirmer.')
        db.add(company); db.flush()
        db.add(CompanyProfileAnswer(company_id=company.id, question_id=question.id, answer_text=text, comment='Recherche documentaire publique ; pas une réponse recueillie auprès de l’entreprise.'))
        for axis in selected_axes:
            db.add(CompanyAxis(company_id=company.id, axis_id=axis.id, is_selected=True, show_in_portfolio=False))
    db.flush()
    return summary
