"""Install the requested questions and one fully answered generated company.

Exact question text is matched within its axis/section. Unknown live questions
abort the transaction rather than receive an unrelated generated answer.
"""
import json
from collections import defaultdict
from pathlib import Path

from sqlalchemy import text

from app.models.axis import Axis
from app.models.axis_question_category import AxisQuestionCategory
from app.models.answer import Answer
from app.models.company import Company
from app.models.company_axis import CompanyAxis
from app.models.company_profile_answer import CompanyProfileAnswer
from app.models.company_profile_question import CompanyProfileQuestion
from app.models.company_profile_section import CompanyProfileSection
from app.models.question import Question
from app.models.score import Score
from app.models.scoring_level import ScoringLevel
from app.models.scoring_scale import ScoringScale
from app.services.public_company_import_service import normalize

DATA_PATH = Path(__file__).resolve().parents[1] / 'data' / 'precision_montelac.json'


def load_montelac():
    return json.loads(DATA_PATH.read_text(encoding='utf-8'))


def one_index(rows, identity):
    result = {}
    for row in rows:
        key = identity(row)
        if key in result:
            raise ValueError(f'Ambiguous records: {key}')
        result[key] = row
    return result


def size_matches(question, size):
    return {'<10': question.target_less_than_10, '11-50': question.target_11_to_50,
            '>50': question.target_more_than_50}[size]


def scoring(db, axis):
    scales = db.query(ScoringScale).filter_by(axis_id=axis.id, is_active=True).all()
    if len(scales) != 1:
        raise ValueError(f'Expected one active scoring scale: {axis.name}')
    scale = scales[0]
    levels = db.query(ScoringLevel).filter_by(scoring_scale_id=scale.id).all()
    return scale, one_index([level for level in levels if level.score_value is not None], lambda l: l.score_value)


def sync_requested_questions(db, case, axes):
    changes = []
    for update in case['question_updates']:
        axis = axes[normalize(update['axis'])]
        identities = {normalize(update['question']), *(normalize(a) for a in update['aliases'])}
        matches = [q for q in db.query(Question).filter_by(axis_id=axis.id)
                   if normalize(q.question_text) in identities]
        if len(matches) > 1:
            raise ValueError(f"Multiple matches for requested question: {update['question']}")
        if matches:
            q = matches[0]
            changed = q.question_text != update['question'] or not q.is_active
            q.question_text = update['question']
            q.is_active = True
            changes.append({'axis': axis.name, 'question_id': q.id,
                            'question': q.question_text, 'action': 'updated' if changed else 'kept'})
        else:
            categories = db.query(AxisQuestionCategory).filter_by(axis_id=axis.id, parent_category_id=None).all()
            categories = [c for c in categories if normalize(c.name) == normalize(update['category'])]
            if len(categories) > 1:
                raise ValueError('Ambiguous question category')
            category = categories[0] if categories else None
            if category is None:
                category = AxisQuestionCategory(axis_id=axis.id, name=update['category'],
                                                order_index=100, is_active=True)
                db.add(category); db.flush()
            if not category.is_active:
                raise ValueError(f'Inactive category: {category.name}')
            maximum = scoring(db, axis)[0].max_score
            order = max((q.order_index for q in db.query(Question).filter_by(axis_id=axis.id)), default=0) + 1
            q = Question(axis_id=axis.id, category_id=category.id, question_text=update['question'],
                         order_index=order, max_score=maximum, is_active=True,
                         target_less_than_10=True, target_11_to_50=True, target_more_than_50=True)
            db.add(q); db.flush()
            changes.append({'axis': axis.name, 'question_id': q.id, 'question': q.question_text, 'action': 'added'})
    db.flush()
    return changes


def question_response(q, axis, index):
    response = index.get((normalize(axis.name), normalize(q.question_text)))
    # A legacy RSE question may contain only the enjeu rather than its statements.
    if response is None and axis.name == 'RSE':
        candidates = [r for (name, _), r in index.items()
                      if name == normalize(axis.name) and normalize(r['question'].split('\n')[0]) == normalize(q.question_text)]
        if len(candidates) == 1:
            response = candidates[0]
    if response is None:
        raise ValueError(f'No specific answer for live question {q.id} [{axis.name}]: {q.question_text}')
    return response


def response_index(responses, scope):
    result = {}
    for response in responses:
        key = (normalize(response[scope]), normalize(response['question']))
        if key in result and (result[key]['answer'] != response['answer'] or result[key].get('score') != response.get('score')):
            raise ValueError(f'Conflicting response templates: {key}')
        result[key] = response
    return result


def calculate_axis(db, company, axis):
    questions = [q for q in db.query(Question).filter_by(axis_id=axis.id, is_active=True)
                 if size_matches(q, company.company_size)]
    ids = [q.id for q in questions]
    answers = db.query(Answer).filter(Answer.company_id == company.id, Answer.question_id.in_(ids)).all()
    if len({a.question_id for a in answers}) != len(answers):
        raise ValueError(f'Duplicate answers for company {company.id}, axis {axis.id}')
    total = sum(a.score_value or 0 for a in answers)
    maximum = sum(q.max_score or 0 for q in questions)
    return {'score_total': total, 'score_max': maximum,
            'score_percentage': round(total / maximum * 100) if maximum else 0,
            'answered_questions': sum(bool(a.score_code) for a in answers), 'total_questions': len(questions)}


def refresh_current_scores(db, affected):
    """Keep archived results; update existing current scores after question changes."""
    rows = (db.query(Score, Company, Axis).join(Company, Score.company_id == Company.id)
            .join(Axis, Score.axis_id == Axis.id).join(CompanyAxis,
                (CompanyAxis.company_id == Company.id) & (CompanyAxis.axis_id == Axis.id))
            .filter(Company.is_archived.is_(False), CompanyAxis.is_selected.is_(True),
                    Axis.id.in_(affected)).all())
    for saved, company, axis in rows:
        for key, value in calculate_axis(db, company, axis).items():
            setattr(saved, key, value)
    db.flush()
    return len(rows)


def install_montelac(db):
    """Caller owns transaction. Repeated calls preserve the existing named company."""
    if db.bind.dialect.name == 'postgresql':
        db.execute(text('SELECT pg_advisory_xact_lock(728462901)'))
    case = load_montelac()
    axes = one_index(db.query(Axis).filter_by(is_active=True).all(), lambda a: normalize(a.name))
    for name in case['axes']:
        if normalize(name) not in axes:
            raise ValueError(f'Missing active axis: {name}')
    changes = sync_requested_questions(db, case, axes)
    changed_axes = {axes[normalize(c['axis'])].id for c in changes if c['action'] != 'kept'}
    refreshed = refresh_current_scores(db, changed_axes) if changed_axes else 0
    matches = [c for c in db.query(Company).all() if normalize(c.name) == normalize(case['name'])]
    if len(matches) > 1:
        raise ValueError('Multiple companies share the requested name')
    summary = {'name': case['name'], 'question_changes': changes, 'current_scores_refreshed': refreshed}
    if matches:
        summary.update(created=False, existing_company_kept=True, company_id=matches[0].id)
        return summary
    responses = response_index(case['axis_responses'], 'axis')
    profiles = response_index(case['profile_responses'], 'section')
    planned = []
    unmapped = []
    for name in case['axes']:
        axis = axes[normalize(name)]
        scale, levels = scoring(db, axis)
        questions = [q for q in db.query(Question).filter_by(axis_id=axis.id, is_active=True)
                     .order_by(Question.order_index, Question.id) if size_matches(q, case['company']['company_size'])]
        if not questions:
            raise ValueError(f'No active questions: {name}')
        for q in questions:
            try:
                response = question_response(q, axis, responses)
            except ValueError:
                unmapped.append({'axis': name, 'question_id': q.id, 'question': q.question_text,
                                 'maximum': q.max_score})
                continue
            desired = response['score']
            # Legacy questions can have a smaller maximum than today's scale.
            value = min(desired, q.max_score) if q.max_score is not None else None
            level = levels.get(value)
            if level is None or not response['answer'].strip():
                raise ValueError(f'Invalid answer or score for question {q.id}')
            planned.append((axis, q, level, response['answer']))
    profile_plan = []
    for q, section in (db.query(CompanyProfileQuestion, CompanyProfileSection)
                       .join(CompanyProfileSection).filter(CompanyProfileQuestion.is_active.is_(True),
                                                         CompanyProfileSection.is_active.is_(True))):
        response = profiles.get((normalize(section.name), normalize(q.question_text)))
        if response is None:
            unmapped.append({'section': section.name, 'question_id': q.id, 'question': q.question_text})
            continue
        profile_plan.append((q, response['answer']))
    if unmapped:
        raise ValueError('No specific answer for live questions: ' + json.dumps(unmapped, ensure_ascii=False))
    company = Company(**case['company'])
    db.add(company); db.flush()
    for axis, q, level, answer in planned:
        db.add(Answer(company_id=company.id, question_id=q.id, score_code=level.code,
                      score_value=level.score_value, answer_text=answer, comment=None))
    for q, answer in profile_plan:
        db.add(CompanyProfileAnswer(company_id=company.id, question_id=q.id, answer_text=answer))
    for name in case['axes']:
        axis = axes[normalize(name)]
        db.add(CompanyAxis(company_id=company.id, axis_id=axis.id, is_selected=True,
                           show_in_portfolio=True, diagnostic_comment=None))
    db.flush()
    scores = []
    for name in case['axes']:
        axis = axes[normalize(name)]
        values = calculate_axis(db, company, axis)
        db.add(Score(company_id=company.id, axis_id=axis.id, **values))
        scores.append({'axis': name, **values})
    db.flush()
    summary.update(created=True, company_id=company.id, axis_answers=len(planned),
                   profile_answers=len(profile_plan), scores=scores)
    return summary
