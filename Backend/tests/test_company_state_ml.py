import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import accuracy_score
from app.models.company import Company
from app.models.score import Score
from app.models.axis import Axis
from app.services import company_state_ml_service as ml


@pytest.fixture
def dataset():
    return ml.build_demo_training_dataset()


@pytest.fixture
def artifacts(tmp_path, monkeypatch):
    monkeypatch.setattr(ml, 'ML_ARTIFACT_DIR', str(tmp_path))
    monkeypatch.setattr(ml, 'MODEL_PATH', str(tmp_path / 'real.joblib'))
    return tmp_path


@pytest.mark.parametrize('problem', ['small', 'missing_column', 'null', 'infinite', 'negative', 'too_high', 'invalid_label', 'rare_class', 'one_class', 'duplicate_company', 'unknown_size', 'non_numeric'])
def test_invalid_datasets_rejected_before_training(dataset, artifacts, problem):
    frame = dataset.copy()
    frame[ml.AXIS_FEATURES] = frame[ml.AXIS_FEATURES].astype(float)
    if problem == 'small': frame = frame.iloc[:8]
    elif problem == 'missing_column': frame = frame.drop(columns=['rh_score'])
    elif problem == 'null': frame.loc[0, 'rh_score'] = np.nan
    elif problem == 'infinite': frame.loc[0, 'rh_score'] = np.inf
    elif problem == 'negative': frame.loc[0, 'rh_score'] = -1
    elif problem == 'too_high': frame.loc[0, 'rh_score'] = 101
    elif problem == 'invalid_label': frame.loc[0, 'target'] = 'blue'
    elif problem == 'rare_class': frame.loc[0, 'target'] = 'red'
    elif problem == 'one_class': frame['target'] = 'red'
    elif problem == 'duplicate_company': frame.loc[0, 'company_id'] = frame.loc[1, 'company_id']
    elif problem == 'unknown_size': frame.loc[0, ml.FEATURE_COLUMNS[7:]] = 0
    elif problem == 'non_numeric': frame['rh_score'] = 'not a score'
    with pytest.raises(ValueError):
        ml.train_model_from_dataset(frame, dataset_source='demo_database_only', use_demo=True)
    assert not list(artifacts.iterdir())


def test_stratified_split_has_no_company_leakage_and_is_reproducible(dataset):
    train, test = ml.split_training_dataset(dataset)
    again_train, again_test = ml.split_training_dataset(dataset)
    assert set(train.company_id).isdisjoint(test.company_id)
    assert len(train) + len(test) == len(dataset)
    assert set(train.target) == set(test.target) == {'green', 'orange', 'red'}
    pd.testing.assert_frame_equal(train, again_train)
    pd.testing.assert_frame_equal(test, again_test)


def test_training_evaluation_and_saved_model_predictions(dataset, artifacts):
    train, test = ml.split_training_dataset(dataset)
    metrics = ml.train_model_from_dataset(dataset, dataset_source='demo_database_only', use_demo=True)
    model = ml.load_model(use_demo=True)
    # The scaler must learn exclusively from training rows, before holdout evaluation.
    np.testing.assert_allclose(model.named_steps['scaler'].mean_, train[ml.FEATURE_COLUMNS].mean().to_numpy())
    np.testing.assert_allclose(model.named_steps['scaler'].var_, train[ml.FEATURE_COLUMNS].var(ddof=0).to_numpy())
    predicted = model.predict(test[ml.FEATURE_COLUMNS])
    assert metrics['accuracy'] == round(accuracy_score(test.target, predicted), 3)
    assert 0 <= metrics['macro_f1'] <= 1
    assert sum(map(sum, metrics['confusion_matrix'])) == len(test)
    assert set(metrics['train_company_ids']).isdisjoint(metrics['test_company_ids'])
    assert metrics == ml.load_metrics(use_demo=True)
    assert metrics['is_demo'] and metrics['dataset_source'] == 'demo_database_only'
    np.testing.assert_allclose(model.predict_proba(test[ml.FEATURE_COLUMNS]).sum(axis=1), 1)
    assert ml.load_model() is None  # Demo training cannot create the real model.
    assert ml.load_metrics() is None


def test_demo_training_does_not_overwrite_real_artifact(dataset, artifacts):
    ml.train_model_from_dataset(dataset, dataset_source='real_database')
    original = (artifacts / 'real.joblib').read_bytes()
    ml.train_model_from_dataset(dataset, dataset_source='demo_database_only', use_demo=True)
    assert (artifacts / 'real.joblib').read_bytes() == original


def test_mismatched_source_rejected(dataset, artifacts):
    with pytest.raises(ValueError, match='source'):
        ml.train_model_from_dataset(dataset, dataset_source='demo_database_only')


def test_real_dataset_excludes_demo_unarchived_and_incomplete_includes_zero(configured_db):
    db = configured_db
    axis = db.query(Axis).filter_by(name='RH').one()
    for name, archived, answered in [('Real completed', True, 2), ('DEMO old record', True, 2), ('Real draft', False, 2), ('Real incomplete', True, 1)]:
        company = Company(name=name, is_archived=archived, general_state='red', company_size='1-10')
        db.add(company); db.flush()
        db.add(Score(company_id=company.id, axis_id=axis.id, score_percentage=0, score_max=10, answered_questions=answered, total_questions=2))
    db.flush()
    real, source = ml.get_training_dataset(db)
    demo, demo_source = ml.get_training_dataset(db, use_demo=True)
    assert len(real) == len(demo) == 1
    assert real.iloc[0]['rh_score'] == 0
    assert real.iloc[0]['company_size_less_10'] == 1
    assert source == 'real_database' and demo_source == 'demo_database_only'
    assert set(real.company_id).isdisjoint(demo.company_id)
    with pytest.raises(ValueError, match='12 complete'):
        ml.train_company_state_model(db)
