"""Create reproducible fictional diagnostics, never overwrite customer records."""
import random
from collections import defaultdict

from app.models.answer import Answer
from app.models.axis import Axis
# Register relationship targets when this service is used by the standalone CLI.
from app.models.axis_question_category import AxisQuestionCategory  # noqa: F401
from app.models.company import Company
from app.models.company_axis import CompanyAxis
from app.models.company_profile_answer import CompanyProfileAnswer
from app.models.company_profile_question import CompanyProfileQuestion
from app.models.company_profile_section import CompanyProfileSection  # noqa: F401
from app.models.question import Question
from app.models.score import Score
from app.models.scoring_level import ScoringLevel
from app.models.scoring_scale import ScoringScale

DEMO_PREFIX = 'DEMO ML - '


def matches_size(question, size):
    return {'<10': question.target_less_than_10, '11-50': question.target_11_to_50, '>50': question.target_more_than_50}[size]


def seed_demo_data(db, *, apply=False, per_class=20, seed=42):
    if not 4 <= per_class <= 500:
        raise ValueError('per_class must be between 4 and 500')
    questions = db.query(Question).join(Axis, Question.axis_id == Axis.id).filter(Question.is_active.is_(True), Axis.is_active.is_(True)).order_by(Question.id).all()
    if not questions:
        raise ValueError('Import and activate the questionnaire first')
    levels = {}
    for axis_id in {q.axis_id for q in questions}:
        scales = db.query(ScoringScale).filter_by(axis_id=axis_id, is_active=True).all()
        if len(scales) != 1:
            raise ValueError('Each scored axis needs exactly one active scale')
        found = db.query(ScoringLevel).filter_by(scoring_scale_id=scales[0].id).all()
        numeric = [l for l in found if l.score_value is not None]
        if not numeric:
            raise ValueError('No numeric scoring levels')
        levels[axis_id] = numeric
    for q in questions:
        if q.max_score <= 0 or any(l.score_value < 0 or l.score_value > q.max_score for l in levels[q.axis_id]):
            raise ValueError(f'Question {q.id} is incompatible with its scoring scale')
    profile_questions = db.query(CompanyProfileQuestion).filter_by(is_active=True).order_by(CompanyProfileQuestion.id).all()
    result = {'companies_added': 0, 'companies_kept': 0, 'fictional': True, 'apply': apply, 'seed': seed}
    for state, mean in [('red', 0.25), ('orange', 0.55), ('green', 0.80)]:
        for index in range(per_class):
            # Stable per-company random streams preserve reproducibility on re-runs.
            rng = random.Random(f'{seed}:{state}:{index}')
            name = f'{DEMO_PREFIX}{state.upper()} - {index + 1:03d}'
            existing = db.query(Company).filter_by(name=name).all()
            if len(existing) > 1:
                raise ValueError(f'Ambiguous demo company: {name}')
            if existing:
                result['companies_kept'] += 1
                continue
            size = ['<10', '11-50', '>50'][index % 3]
            selected = [q for q in questions if matches_size(q, size)]
            if not selected:
                raise ValueError(f'No active questions for company size {size}')
            result['companies_added'] += 1
            if not apply:
                continue
            company = Company(name=name, company_size=size, status='Client', is_archived=True, general_state=state, general_comment='DONNÉES FICTIVES — démonstration ML. État simulé, non validé par un expert. Ne pas renommer cette entreprise.')
            db.add(company)
            db.flush()
            by_axis = defaultdict(list)
            persona = max(0, min(1, rng.gauss(mean, 0.10)))
            for q in selected:
                ratio = max(0, min(1, rng.gauss(persona, 0.20)))
                chosen = min(levels[q.axis_id], key=lambda l: abs(l.score_value / q.max_score - ratio))
                db.add(Answer(company_id=company.id, question_id=q.id, score_code=chosen.code, score_value=chosen.score_value, comment='Réponse fictive générée pour tester le pipeline.'))
                by_axis[q.axis_id].append((q, chosen.score_value))
            for axis_id, pairs in by_axis.items():
                total = sum(value for _, value in pairs)
                maximum = sum(q.max_score for q, _ in pairs)
                db.add(CompanyAxis(company_id=company.id, axis_id=axis_id, is_selected=True))
                db.add(Score(company_id=company.id, axis_id=axis_id, score_total=total, score_max=maximum, score_percentage=round(total / maximum * 100, 2), answered_questions=len(pairs), total_questions=len(pairs)))
            for question in profile_questions:
                db.add(CompanyProfileAnswer(company_id=company.id, question_id=question.id, answer_text='Exemple fictif : contexte à remplacer par les observations du consultant.', comment='Données de démonstration uniquement.'))
    if apply:
        db.flush()
    return result
