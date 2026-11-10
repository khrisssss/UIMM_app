"""Tests for the one-time database setup (axes, scoring scales, first admin)."""
import pytest

from app.models.axis import Axis
from app.models.scoring_level import ScoringLevel
from app.models.scoring_scale import ScoringScale
from app.models.user import User
from app.services.security import verify_password
from app.setup_database import create_axes_and_scales, create_first_admin


def test_creates_six_axes_with_their_scales(db):
    added = create_axes_and_scales(db)

    assert added == {"axes": 6, "scoring_scales": 6, "scoring_levels": 5 * 6 + 5}
    assert [axis.name for axis in db.query(Axis).order_by(Axis.order_index)] == [
        "Stratégie", "Performance", "Marketing", "RH", "Digitalisation", "RSE"]
    rse = db.query(Axis).filter_by(name="RSE").one()
    rse_scale = db.query(ScoringScale).filter_by(axis_id=rse.id).one()
    assert rse_scale.max_score == 3
    assert db.query(ScoringLevel).filter_by(scoring_scale_id=rse_scale.id, code="SO").one().score_value is None


def test_running_twice_adds_nothing(db):
    create_axes_and_scales(db)

    assert create_axes_and_scales(db) == {"axes": 0, "scoring_scales": 0, "scoring_levels": 0}
    assert db.query(Axis).count() == 6


def test_first_admin_is_created_once_with_hashed_password(db):
    assert create_first_admin(db, "admin@uimm.local", "a-long-test-password") is True
    db.flush()
    admin = db.query(User).one()
    assert admin.role == "admin" and admin.is_active
    assert admin.hashed_password != "a-long-test-password"
    assert verify_password("a-long-test-password", admin.hashed_password)

    assert create_first_admin(db, "admin@uimm.local", "a-long-test-password") is False
    assert db.query(User).count() == 1


def test_short_admin_password_is_refused(db):
    with pytest.raises(ValueError):
        create_first_admin(db, "admin@uimm.local", "admin123")
    assert db.query(User).count() == 0
