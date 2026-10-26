"""Add the Power Apps bank without deleting questions, answers or scoring scales.

The caller owns the transaction. A preview performs reads only. Re-imports match
axis/section and normalized text; source IDs never replace database primary keys.
"""
import json
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

from app.models.axis import Axis
from app.models.axis_question_category import AxisQuestionCategory
from app.models.company_profile_question import CompanyProfileQuestion
from app.models.company_profile_section import CompanyProfileSection
from app.models.question import Question
from app.models.scoring_scale import ScoringScale

BANK_PATH = Path(__file__).resolve().parents[1] / 'data' / 'powerapps_questionnaire.json'


def key(value):
    return ' '.join(unicodedata.normalize('NFKC', value).casefold().split())


def load_bank():
    from app.services.diagnostic_scope_service import is_finance_name
    return [record for record in json.loads(BANK_PATH.read_text(encoding='utf-8'))['questions']
            if not is_finance_name(record.get('Axe') or record.get('Section') or '')]


def question_text(record):
    if 'Enjeu' in record:
        return record['Enjeu'] + '\n\n' + record['Affirmations']
    return record['Question']


def unique_index(items, identity):
    result = {}
    for item in items:
        identity_key = identity(item)
        if identity_key in result:
            raise ValueError(f'Ambiguous existing records: {identity_key}. Resolve duplicates before import.')
        result[identity_key] = item
    return result


def import_questionnaire(db, *, apply=False, activate=False, records=None):
    records = load_bank() if records is None else records
    axes = unique_index(db.query(Axis).all(), lambda a: key(a.name))
    sections = unique_index(db.query(CompanyProfileSection).all(), lambda s: key(s.name))
    all_categories = db.query(AxisQuestionCategory).all()
    category_names = {c.id: key(c.name) for c in all_categories}
    categories = unique_index([c for c in all_categories if c.parent_category_id is None], lambda c: (c.axis_id, key(c.name)))
    source_groups = Counter((axes[key(r['Axe'])].id, key(r.get('Domaine') or r.get('Categorie') or 'Général'), key(question_text(r))) for r in records if 'Axe' in r and key(r['Axe']) in axes)
    def question_identity(axis_id, category, text, order):
        group = (axis_id, category, key(text))
        return (*group, order if source_groups[group] > 1 else None)
    question_rows = db.query(Question).all()
    questions = unique_index(question_rows, lambda q: question_identity(q.axis_id, category_names.get(q.category_id, ""), q.question_text, q.order_index))
    source_text_counts = Counter((key(r['Axe']), key(question_text(r))) for r in records if 'Axe' in r)
    existing_by_text = defaultdict(list)
    for q in question_rows:
        existing_by_text[(q.axis_id, key(q.question_text))].append(q)
    profiles = unique_index(db.query(CompanyProfileQuestion).all(), lambda q: (q.section_id, key(q.question_text)))
    scales = {}
    for name in {r['Axe'] for r in records if 'Axe' in r}:
        axis = axes.get(key(name))
        if axis is None or not axis.is_active:
            raise ValueError(f'Missing active axis: {name}. Configure axes before import.')
        found = db.query(ScoringScale).filter_by(axis_id=axis.id, is_active=True).all()
        if len(found) != 1 or found[0].max_score <= 0:
            raise ValueError(f'Expected one active scoring scale for {name}. Configure scoring before import.')
        scales[axis.id] = found[0].max_score
    summary = {'axis_questions_added': 0, 'profile_questions_added': 0, 'existing_questions_kept': 0, 'apply': apply, 'new_questions_active': activate}
    seen = set()
    for r in records:
        text = question_text(r)
        scope = ('axis', key(r['Axe']), key(r.get('Domaine') or r.get('Categorie') or 'Général')) if 'Axe' in r else ('profile', key(r['Section']))
        source_key = (*scope, key(text), r['Ordre'])
        if source_key in seen:
            raise ValueError(f'Duplicate question in source: {source_key}')
        seen.add(source_key)
        if 'Axe' in r:
            axis = axes[key(r['Axe'])]
            category_name = r.get('Domaine') or r.get('Categorie') or 'Général'
            identity = question_identity(axis.id, key(category_name), text, r['Ordre'])
            legacy = existing_by_text.get((axis.id, key(text)), [])
            # A single old uncategorized question can be reused when the source
            # text is unambiguous. Repeated text in different categories stays distinct.
            reuse_legacy = source_text_counts[(key(r['Axe']), key(text))] == 1 and len(legacy) == 1
            if identity in questions or reuse_legacy:
                summary['existing_questions_kept'] += 1
                continue
            summary['axis_questions_added'] += 1
            if apply:
                category_name = r.get('Domaine') or r.get('Categorie') or 'Général'
                category_key = (axis.id, key(category_name))
                if category_key not in categories:
                    category = AxisQuestionCategory(axis_id=axis.id, name=category_name, order_index=r['Ordre'], is_active=True)
                    db.add(category)
                    db.flush()
                    categories[category_key] = category
                if not categories[category_key].is_active:
                    raise ValueError(f'Category is inactive: {category_name}. Review it before import.')
                item = Question(axis_id=axis.id, category_id=categories[category_key].id, question_text=text, order_index=r['Ordre'], max_score=scales[axis.id], is_active=activate, target_less_than_10=r.get('CibleMoins10', True), target_11_to_50=r.get('Cible10_50', True), target_more_than_50=r.get('CiblePlus50', True))
                db.add(item)
                questions[identity] = item
        else:
            section_key = key(r['Section'])
            section = sections.get(section_key)
            identity = (section.id, key(text)) if section else None
            if identity in profiles:
                summary['existing_questions_kept'] += 1
                continue
            summary['profile_questions_added'] += 1
            if apply:
                if section is None:
                    section = CompanyProfileSection(name=r['Section'], order_index=len(sections) + 1, is_active=True)
                    db.add(section)
                    db.flush()
                    sections[section_key] = section
                if not section.is_active:
                    raise ValueError(f'Profile section is inactive: {section.name}. Review it before import.')
                item = CompanyProfileQuestion(section_id=section.id, question_text=text, order_index=r['Ordre'], is_active=activate)
                db.add(item)
                profiles[(section.id, key(text))] = item
    if apply:
        db.flush()
    return summary
