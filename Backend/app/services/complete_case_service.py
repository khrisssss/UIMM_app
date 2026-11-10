"""One fully answered fictional case for the six-axis diagnostic workflow."""
import json
import re
from pathlib import Path
from collections import defaultdict

from app.models.company import Company
from app.models.axis import Axis
from app.models.question import Question
from app.models.axis_question_category import AxisQuestionCategory  # noqa: F401 -- standalone mapper target
from app.models.answer import Answer
from app.models.company_axis import CompanyAxis
from app.models.company_profile_section import CompanyProfileSection
from app.models.company_profile_question import CompanyProfileQuestion
from app.models.company_profile_answer import CompanyProfileAnswer
from app.models.scoring_scale import ScoringScale
from app.models.scoring_level import ScoringLevel
from app.models.score import Score
from app.services.public_company_import_service import normalize

CASE_PATH = Path(__file__).resolve().parents[1] / 'data' / 'complete_case_study.json'


def load_case():
    return json.loads(CASE_PATH.read_text(encoding='utf-8'))


def matches_size(question, size):
    return {'<10': question.target_less_than_10, '11-50': question.target_11_to_50, '>50': question.target_more_than_50}[size]


def contains(text, keyword):
    text, keyword = normalize(text), normalize(keyword)
    return bool(re.search(r'(?<!\w)' + re.escape(keyword) + r'(?!\w)', text)) if len(keyword) <= 3 else keyword in text


def axis_response(question, axis_case):
    topic = question.question_text + ' ' + (question.category.name if question.category else '')
    for rule in axis_case['rules']:
        if any(contains(topic, keyword) for keyword in rule['keywords']):
            return rule['score'], rule['answer']
    return axis_case['score'], axis_case['answer']


def profile_response(question, case):
    for keywords, answer in case['profile_answers']:
        if any(contains(question.question_text, keyword) for keyword in keywords):
            return answer
    return f"Cas fictif : {case['activity']} Équipe de 28 salariés, petites séries traçables et dépendance au premier client (42 % du CA). Le suivi commercial et de production est manuel. Cette réponse de cadrage est générée pour le cas d’étude, pas recueillie auprès d’une entreprise réelle."


def create_complete_case(db, *, apply=False):
    """Caller owns the transaction. Existing named records are never overwritten."""
    case = load_case()
    existing = [c for c in db.query(Company).all() if normalize(c.name) == normalize(case['name'])]
    if len(existing) > 1:
        raise ValueError('Multiple existing companies share the case name; review before creating the case')
    if existing:
        return {'apply': apply, 'created': False, 'existing_company_kept': True, 'company_id': existing[0].id, 'name': existing[0].name}
    active_axes = db.query(Axis).filter_by(is_active=True).all()
    axes_by_name = {normalize(a.name): a for a in active_axes}
    selected = []
    for name, axis_case in case['axes'].items():
        axis = axes_by_name.get(normalize(name))
        if axis is None:
            raise ValueError(f'Missing active axis: {name}')
        questions = db.query(Question).filter_by(axis_id=axis.id, is_active=True).order_by(Question.order_index, Question.id).all()
        questions = [q for q in questions if matches_size(q, case['company_size'])]
        if not questions:
            raise ValueError(f'No active questions for {name}; import the questionnaire first')
        scales = db.query(ScoringScale).filter_by(axis_id=axis.id, is_active=True).all()
        if len(scales) != 1:
            raise ValueError(f'Expected one active scoring scale for {name}')
        levels = [l for l in db.query(ScoringLevel).filter_by(scoring_scale_id=scales[0].id) if l.score_value is not None]
        for question in questions:
            allowed = [l for l in levels if 0 <= l.score_value <= question.max_score]
            if not allowed:
                raise ValueError(f'No valid scoring level for question {question.id}')
            desired, answer = axis_response(question, axis_case)
            chosen = min(allowed, key=lambda level: (abs(level.score_value - desired), level.order_index))
            if name == 'RSE':
                statements = [line.strip() for line in question.question_text.splitlines() if line.strip().startswith('•')]
                if statements:
                    count = min(chosen.score_value, len(statements))
                    answer = f"Dans ce cas fictif, {count} affirmation(s) sont considérées satisfaites :\n" + '\n'.join(statements[:count]) + '\nLes autres affirmations ne sont pas encore satisfaites. Il s’agit d’hypothèses du cas d’étude.'
            selected.append((axis, question, chosen, answer))
    profile_questions = db.query(CompanyProfileQuestion).join(CompanyProfileSection).filter(CompanyProfileQuestion.is_active.is_(True), CompanyProfileSection.is_active.is_(True)).order_by(CompanyProfileSection.order_index, CompanyProfileQuestion.order_index).all()
    summary = {'apply': apply, 'created': False, 'name': case['name'], 'case_study': True, 'fictional': True, 'axis_count': len(case['axes']), 'axis_answers': len(selected), 'profile_answers': len(profile_questions), 'scores': []}
    by_axis = defaultdict(list)
    for axis, question, level, answer in selected:
        by_axis[axis.id].append((axis, question, level, answer))
    for pairs in by_axis.values():
        total = sum(level.score_value for _, _, level, _ in pairs)
        maximum = sum(question.max_score for _, question, _, _ in pairs)
        summary['scores'].append({'axis': pairs[0][0].name, 'score_total': total, 'score_max': maximum, 'score_percentage': round(total / maximum * 100), 'answered_questions': len(pairs), 'total_questions': len(pairs)})
    if not apply:
        return summary
    company = Company(name=case['name'], is_synthetic=True, company_size=case['company_size'], address='Agglomération toulousaine — localisation fictive du cas d’étude', status='Prospect', is_archived=False, general_state='orange', has_rse=True, general_comment=case['context'])
    db.add(company); db.flush()
    for axis, question, level, answer in selected:
        db.add(Answer(company_id=company.id, question_id=question.id, score_code=level.code, score_value=level.score_value, answer_text=answer, comment='Réponse et note générées pour un cas d’étude fictif ; consulter le contexte dans le profil de l’entreprise.'))
    for profile in profile_questions:
        db.add(CompanyProfileAnswer(company_id=company.id, question_id=profile.id, answer_text=profile_response(profile, case), comment='Réponse générée dans le cadre du cas d’étude fictif.'))
    summaries = {s['axis']: s for s in summary['scores']}
    for pairs in by_axis.values():
        axis = pairs[0][0]
        score = summaries[axis.name]
        db.add(CompanyAxis(company_id=company.id, axis_id=axis.id, is_selected=True, show_in_portfolio=True, diagnostic_comment=case['axes'][axis.name]['answer']))
        db.add(Score(company_id=company.id, axis_id=axis.id, **{k: v for k, v in score.items() if k != 'axis'}))
    db.flush()
    summary.update({'created': True, 'company_id': company.id})
    return summary
