"""Exercise the standalone command without the models preloaded by conftest."""
import os
from pathlib import Path
import subprocess
import sys
import textwrap


def test_seed_command_registers_models_and_previews_then_applies():
    program = textwrap.dedent('''
        import contextlib
        import io
        import json
        import sys
        # Import only the command's own dependency graph, as on the VPS.
        import app.scripts.seed_ml_demo_data
        from app.database import Base, engine, SessionLocal
        from app.models.axis import Axis
        from app.models.question import Question
        from app.models.company import Company
        from app.models.scoring_scale import ScoringScale
        from app.models.scoring_level import ScoringLevel
        from sqlalchemy.orm import configure_mappers
        configure_mappers()
        Base.metadata.create_all(engine)
        with SessionLocal() as db:
            axis = Axis(name='RH', order_index=1)
            db.add(axis)
            db.flush()
            scale = ScoringScale(axis_id=axis.id, name='Test', max_score=5)
            db.add(scale)
            db.flush()
            db.add(ScoringLevel(scoring_scale_id=scale.id, code='3', score_value=3, label='Partial', order_index=3))
            db.add(Question(axis_id=axis.id, question_text='Test question', max_score=5))
            db.commit()
        for apply, expected in [(False, 0), (True, 12)]:
            sys.argv = ['seed_ml_demo_data', '--per-class', '4'] + (['--apply'] if apply else [])
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                app.scripts.seed_ml_demo_data.main()
            result = json.loads(output.getvalue())
            assert result['companies_added'] == 12
            assert result['apply'] is apply
            with SessionLocal() as db:
                assert db.query(Company).count() == expected
    ''')
    environment = {**os.environ, 'DATABASE_URL': 'sqlite://'}
    result = subprocess.run([sys.executable, '-c', program], cwd=Path(__file__).resolve().parents[1], env=environment, text=True, capture_output=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
