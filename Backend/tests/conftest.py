"""Tests always use isolated SQLite; they never open the application's database."""
import os
os.environ['DATABASE_URL'] = 'sqlite://'

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from app.database import Base
from app.models.axis import Axis
from app.models.axis_question_category import AxisQuestionCategory  # noqa: F401
from app.models.company_profile_section import CompanyProfileSection  # noqa: F401
from app.models.company_profile_question import CompanyProfileQuestion  # noqa: F401
from app.models.company_profile_answer import CompanyProfileAnswer  # noqa: F401
from app.models.company_axis import CompanyAxis  # noqa: F401
from app.models.company import Company  # noqa: F401
from app.models.question import Question  # noqa: F401
from app.models.answer import Answer  # noqa: F401
from app.models.score import Score  # noqa: F401
from app.models.scoring_scale import ScoringScale
from app.models.scoring_level import ScoringLevel


@pytest.fixture
def db():
    engine = create_engine('sqlite://')
    @event.listens_for(engine, 'connect')
    def foreign_keys(connection, _):
        connection.execute('PRAGMA foreign_keys=ON')
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
        session.rollback()
    engine.dispose()


@pytest.fixture
def configured_db(db):
    for index, name in enumerate(['Stratégie', 'Performance', 'Marketing', 'RH', 'Finance', 'Digitalisation', 'RSE'], 1):
        axis = Axis(name=name, order_index=index, is_active=True)
        db.add(axis)
        db.flush()
        if name == 'Finance':
            continue
        maximum = 3 if name == 'RSE' else 5
        scale = ScoringScale(axis_id=axis.id, name=f'Test {name}', max_score=maximum, is_active=True)
        db.add(scale)
        db.flush()
        for score in range(maximum + 1):
            db.add(ScoringLevel(scoring_scale_id=scale.id, code=str(score), score_value=score, label=str(score), order_index=score))
    db.commit()
    return db
