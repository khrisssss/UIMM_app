from copy import deepcopy
import json
from pathlib import Path
import pytest
from app.models.answer import Answer
from app.models.company import Company
from app.models.company_profile_answer import CompanyProfileAnswer
from app.models.score import Score
from app.models.question import Question
from app.models.axis import Axis
from app.models.company_profile_section import CompanyProfileSection
from app.models.company_profile_question import CompanyProfileQuestion
from app.scripts.install_mecanique_solerive import load_solerive
from app.services.montelac_import_service import install_answered_company, install_montelac, calculate_axis
from app.services.questionnaire_import_service import import_questionnaire


def test_new_company_has_all_answers_comments_scores_and_keeps_montelac(configured_db):
    db = configured_db
    import_questionnaire(db, apply=True, activate=True); db.commit()
    existing = install_montelac(db); db.commit()
    before = [(a.id,a.answer_text,a.comment,a.score_value) for a in db.query(Answer).filter_by(company_id=existing['company_id']).order_by(Answer.id)]
    case = load_solerive()
    result = install_answered_company(db, case); db.commit()
    company = db.get(Company, result['company_id'])
    assert company.name == 'Mécanique Solérive' and company.contact_name == 'Mathieu Delmas'
    assert result['axis_answers'] == result['axis_comments'] == 201
    assert result['profile_answers'] == result['profile_comments'] == 20
    assert db.query(Company).count() == 2
    assert all(a.answer_text and a.comment and a.score_code is not None for a in db.query(Answer).filter_by(company_id=company.id))
    assert all(a.answer_text and a.comment for a in db.query(CompanyProfileAnswer).filter_by(company_id=company.id))
    for saved in db.query(Score).filter_by(company_id=company.id):
        expected = calculate_axis(db, company, db.get(Axis, saved.axis_id))
        assert all(getattr(saved,key)==value for key,value in expected.items())
        assert saved.answered_questions == saved.total_questions
    assert [(a.id,a.answer_text,a.comment,a.score_value) for a in db.query(Answer).filter_by(company_id=existing['company_id']).order_by(Answer.id)] == before
    again = install_answered_company(db, case)
    assert again['existing_company_kept'] and db.query(Company).count() == 2


def test_live_wordings_are_covered_with_comments(configured_db):
    db = configured_db
    import_questionnaire(db, apply=True, activate=True); db.commit()
    live = json.loads((Path(__file__).parent/'fixtures'/'montelac_live_questions.json').read_text())
    for item in live:
        if 'axis' in item:
            axis = db.query(Axis).filter_by(name=item['axis']).one()
            db.add(Question(axis_id=axis.id,question_text=item['question'],max_score=item['maximum'],is_active=True))
        else:
            section = db.query(CompanyProfileSection).filter_by(name=item['section']).one()
            db.add(CompanyProfileQuestion(section_id=section.id,question_text=item['question'],is_active=True))
    db.commit()
    result = install_answered_company(db,load_solerive());db.commit()
    assert result['axis_comments']==result['axis_answers']==255
    assert result['profile_comments']==result['profile_answers']==22


def test_missing_comment_fails_without_partial_company(configured_db):
    db = configured_db
    import_questionnaire(db,apply=True,activate=True);db.commit()
    case=deepcopy(load_solerive())
    for r in case['axis_responses']:r.pop('comment',None)
    with pytest.raises(ValueError,match='Missing comment'):
        install_answered_company(db,case)
    db.rollback()
    assert db.query(Company).count()==0 and db.query(Answer).count()==0


def test_dataset_financial_and_operating_consistency():
    case=load_solerive()
    assert case['employee_count']==24 and case['company']['company_size']=='11-50'
    rows=case['axis_responses']+case['profile_responses']
    assert all(r.get('answer') and r.get('comment') for r in rows)
    byid={r.get('source_question_id'):r for r in rows if r.get('source_question_id')}
    assert '3 600 000' in byid[3]['answer'] and '12,5 %' in byid[3]['answer']
    assert 252000-102000==150000 and 96000+102000==198000
    assert 2520000+720000+360000==3600000
    assert 'Pas de CRM' in byid[3007]['answer'] and byid[6042]['answer']==byid[3007]['answer']
    assert byid[6041]['answer']==byid[3014]['answer']
    assert '86 %' in byid[3016]['answer']
    for r in rows:
        if r.get('source_question_id',0)>=7001:
            assert r['score']==sum(line.startswith('Satisfaite :') for line in r['answer'].splitlines())
