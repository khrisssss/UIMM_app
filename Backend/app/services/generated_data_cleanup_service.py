"""Remove explicitly generated companies and the retired public-research question."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from sqlalchemy import or_
from app.services.company_details_service import record_details
from app.models.company import Company
from app.models.answer import Answer
from app.models.score import Score
from app.models.swot import SWOT
from app.models.reports import Report
from app.models.company_axis import CompanyAxis
from app.models.financial_year import FinancialYear
from app.models.company_profile_question import CompanyProfileQuestion
from app.models.company_profile_answer import CompanyProfileAnswer
from app.services.public_company_import_service import PROFILE_QUESTION, normalize

CHILD_MODELS = [Answer, Score, SWOT, Report, CompanyAxis, FinancialYear]


def identify_generated_companies(db):
    questions = [q for q in db.query(CompanyProfileQuestion).all() if normalize(q.question_text) == normalize(PROFILE_QUESTION)]
    question_ids = [q.id for q in questions]
    imported_ids = {
        answer.company_id for answer in db.query(CompanyProfileAnswer).filter(CompanyProfileAnswer.question_id.in_(question_ids)).all()
        if (answer.comment or '').startswith('Recherche documentaire publique ;')
    } if question_ids else set()
    targets = []
    for company in db.query(Company).order_by(Company.id):
        name, comment = company.name.strip(), company.general_comment or ''
        reason = None
        if bool(getattr(company, 'is_synthetic', False)):
            reason = 'generated_case_or_sample'
        elif name.startswith(('DEMO ML - ', 'DEMO — ')) or comment.startswith('[CAS_FICTIF]'):
            reason = 'known_generated_case_marker'
        elif company.id in imported_ids or (comment.startswith('Activité publiée : ') and 'Fiche documentaire publique. Aucun entretien ou diagnostic réalisé' in comment):
            reason = 'imported_public_profile'
        if reason:
            targets.append({'id': company.id, 'name': company.name, 'reason': reason})
    return targets, questions


def cleanup_generated_data(db, *, apply=False, backup_directory='generated_reports/cleanup_backups'):
    """Caller owns the transaction. A private backup must succeed before deletion."""
    targets, questions = identify_generated_companies(db)
    ids = [item['id'] for item in targets]
    question_ids = [q.id for q in questions]
    profile_condition = or_(CompanyProfileAnswer.company_id.in_(ids), CompanyProfileAnswer.question_id.in_(question_ids))
    summary = {'apply': apply, 'companies_to_remove': targets, 'company_count': len(ids), 'public_research_questions': len(question_ids), 'deleted_companies': 0, 'deleted_profile_questions': 0}
    if not apply or (not ids and not question_ids):
        return summary
    # Prevent writes/deletion of the targeted company rows while backing them up.
    companies = db.query(Company).filter(Company.id.in_(ids)).with_for_update().all() if ids else []
    backup = {'created_at': datetime.now(timezone.utc).isoformat(), 'purpose': 'User-requested generated-data cleanup', 'tables': {
        Company.__tablename__: [record_details(c) for c in companies],
        CompanyProfileQuestion.__tablename__: [record_details(q) for q in questions],
        CompanyProfileAnswer.__tablename__: [record_details(a) for a in db.query(CompanyProfileAnswer).filter(profile_condition).all()],
    }}
    for model in CHILD_MODELS:
        backup['tables'][model.__tablename__] = [record_details(row) for row in db.query(model).filter(model.company_id.in_(ids)).all()]
    directory = Path(backup_directory)
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = directory / f"generated-data-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}-{uuid4().hex[:8]}.json"
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, 'w', encoding='utf-8') as output:
        json.dump(backup, output, ensure_ascii=False, indent=2)
        output.flush()
        os.fsync(output.fileno())
    summary['backup'] = str(path)
    summary['deleted_linked_records'] = {}
    summary['deleted_linked_records'][CompanyProfileAnswer.__tablename__] = db.query(CompanyProfileAnswer).filter(profile_condition).delete(synchronize_session=False)
    for model in CHILD_MODELS:
        summary['deleted_linked_records'][model.__tablename__] = db.query(model).filter(model.company_id.in_(ids)).delete(synchronize_session=False)
    summary['deleted_profile_questions'] = db.query(CompanyProfileQuestion).filter(CompanyProfileQuestion.id.in_(question_ids)).delete(synchronize_session=False)
    summary['deleted_companies'] = db.query(Company).filter(Company.id.in_(ids)).delete(synchronize_session=False)
    return summary
