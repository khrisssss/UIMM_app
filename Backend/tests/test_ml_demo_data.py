import pytest
from app.models.answer import Answer
from app.models.axis import Axis
from app.models.company import Company
from app.models.company_axis import CompanyAxis
from app.models.company_profile_answer import CompanyProfileAnswer
from app.models.score import Score
from app.models.question import Question
from app.services.questionnaire_import_service import import_questionnaire
from app.services.ml_demo_data_service import seed_demo_data
from app.services import company_state_ml_service as ml


def test_demo_seed_preview_and_idempotency_and_score_consistency(configured_db):
    db = configured_db
    import_questionnaire(db, apply=True, activate=True)
    real = Company(name='Existing customer', general_state='orange')
    db.add(real); db.commit()
    preview = seed_demo_data(db, per_class=4)
    assert preview['companies_added'] == 12
    assert db.query(Company).count() == 1
    first = seed_demo_data(db, apply=True, per_class=4)
    db.commit()
    assert first['companies_added'] == 12
    again = seed_demo_data(db, apply=True, per_class=4)
    assert again['companies_added'] == 0 and again['companies_kept'] == 12
    assert real.name == 'Existing customer' and real.general_state == 'orange'
    assert db.query(Company).count() == 13
    assert db.query(CompanyProfileAnswer).count() == 12 * 20
    for score in db.query(Score).all():
        pairs = db.query(Answer, Question).join(Question, Answer.question_id == Question.id).filter(Answer.company_id == score.company_id, Question.axis_id == score.axis_id).all()
        assert score.score_total == sum(a.score_value for a, _ in pairs)
        assert score.score_max == sum(q.max_score for _, q in pairs)
        assert score.score_percentage == round(score.score_total / score.score_max * 100, 2)
        assert score.answered_questions == score.total_questions == len(pairs)
    assert len(ml.training_dataset(db, use_demo=True)) == 12
    assert ml.training_dataset(db).empty


def test_end_to_end_import_seed_train_reload_predict(configured_db, tmp_path, monkeypatch):
    db = configured_db
    monkeypatch.setattr(ml, 'ML_ARTIFACT_DIR', str(tmp_path))
    monkeypatch.setattr(ml, 'MODEL_PATH', str(tmp_path / 'real.joblib'))
    import_questionnaire(db, apply=True, activate=True)
    seed_demo_data(db, apply=True, per_class=20)
    db.commit()
    metrics = ml.train_company_state_model(db, use_demo=True)
    assert metrics['dataset_size'] == 60
    assert metrics['train_size'] == 45 and metrics['test_size'] == 15
    company = db.query(Company).order_by(Company.id).first()
    original_label = company.general_state
    prediction = ml.predict_company_state(db, company.id)
    assert prediction['is_demo']
    assert prediction['model_source'] == 'demo_database_only'
    assert prediction['predicted_state'] in ml.STATE_LABELS
    assert abs(sum(p['probability'] for p in prediction['probabilities'].values()) - 1) < 0.002
    assert company.general_state == original_label
    real = Company(name='Real customer', company_size='<10')
    db.add(real); db.flush()
    with pytest.raises(ValueError, match='real model'):
        ml.predict_company_state(db, real.id)
    with pytest.raises(ValueError, match='not found'):
        ml.predict_company_state(db, 99999)


def test_seed_requires_active_questions_and_valid_count(configured_db):
    with pytest.raises(ValueError, match='activate'):
        seed_demo_data(configured_db)
    with pytest.raises(ValueError, match='per_class'):
        seed_demo_data(configured_db, per_class=1)
