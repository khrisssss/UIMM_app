"""Fill blank question comments for the existing Précision Montelac record."""
from sqlalchemy import text
from app.models.answer import Answer
from app.models.axis import Axis
from app.models.company import Company
from app.models.company_profile_answer import CompanyProfileAnswer
from app.models.company_profile_question import CompanyProfileQuestion
from app.models.company_profile_section import CompanyProfileSection
from app.models.question import Question
from app.services.montelac_import_service import load_montelac, response_index, question_response
from app.services.public_company_import_service import normalize


def fill_montelac_comments(db, *, company_id=102):
    """Caller owns transaction. Preserve answers, scores and nonempty comments."""
    if db.bind.dialect.name == 'postgresql':
        db.execute(text('SELECT pg_advisory_xact_lock(728462901)'))
    case = load_montelac()
    company = db.query(Company).filter_by(id=company_id).with_for_update().one_or_none()
    if company is None or normalize(company.name) != normalize(case['name']) or not company.is_synthetic:
        raise ValueError('The expected generated Précision Montelac company was not found; no comments changed')
    axes = response_index(case['axis_responses'], 'axis')
    profiles = response_index(case['profile_responses'], 'section')
    axis_rows = (db.query(Answer, Question, Axis).join(Question, Answer.question_id == Question.id)
                 .join(Axis, Question.axis_id == Axis.id).filter(Answer.company_id == company.id)
                 .with_for_update(of=Answer).all())
    profile_rows = (db.query(CompanyProfileAnswer, CompanyProfileQuestion, CompanyProfileSection)
                    .join(CompanyProfileQuestion, CompanyProfileAnswer.question_id == CompanyProfileQuestion.id)
                    .join(CompanyProfileSection, CompanyProfileQuestion.section_id == CompanyProfileSection.id)
                    .filter(CompanyProfileAnswer.company_id == company.id)
                    .with_for_update(of=CompanyProfileAnswer).all())
    if not axis_rows or not profile_rows:
        raise ValueError('Expected saved axis and profile answers before adding comments')
    planned = []
    preserved = {'axis': 0, 'profile': 0}
    unmatched = []
    for answer, question, axis in axis_rows:
        if (answer.comment or '').strip():
            preserved['axis'] += 1
            continue
        try:
            response = question_response(question, axis, axes)
        except ValueError:
            response = None
        if response is None or response['answer'].strip() != (answer.answer_text or '').strip() or not response.get('comment', '').strip():
            unmatched.append({'scope': axis.name, 'question_id': question.id})
            continue
        planned.append(('axis', answer, response['comment']))
    for answer, question, section in profile_rows:
        if (answer.comment or '').strip():
            preserved['profile'] += 1
            continue
        response = profiles.get((normalize(section.name), normalize(question.question_text)))
        if response is None or response['answer'].strip() != (answer.answer_text or '').strip() or not response.get('comment', '').strip():
            unmatched.append({'scope': section.name, 'profile_question_id': question.id})
            continue
        planned.append(('profile', answer, response['comment']))
    if unmatched:
        raise ValueError(f'Question or answer changed; prepare a matching comment before updating: {unmatched}')
    for _, answer, comment in planned:
        answer.comment = comment
    db.flush()
    summary = {'company_id': company.id, 'name': company.name,
               'axis_comments_added': sum(scope == 'axis' for scope, _, _ in planned),
               'profile_comments_added': sum(scope == 'profile' for scope, _, _ in planned),
               'axis_comments_preserved': preserved['axis'], 'profile_comments_preserved': preserved['profile'],
               'axis_answers': len(axis_rows), 'profile_answers': len(profile_rows),
               'all_axis_comments_filled': all((a.comment or '').strip() for a, _, _ in axis_rows),
               'all_profile_comments_filled': all((a.comment or '').strip() for a, _, _ in profile_rows)}
    if not summary['all_axis_comments_filled'] or not summary['all_profile_comments_filled']:
        raise ValueError('Comment verification failed')
    return summary
