"""Prepare an empty database: the six diagnostic axes, their scoring scales, and the first admin.

Safe to run several times: anything that already exists is left unchanged.

Usage (from the Backend folder, with DATABASE_URL set in .env):
    ADMIN_USERNAME=admin@uimm.local ADMIN_PASSWORD='a-long-password' python -m app.setup_database

The admin password is read from the environment and is never stored in the code.
"""
import os
import sys

from app.database import Base, SessionLocal, engine
from app.models.axis import Axis
from app.models.axis_question_category import AxisQuestionCategory  # noqa: F401  (registers the Question.category relationship)
from app.models.question import Question  # noqa: F401  (registers the Axis.questions relationship)
from app.models.scoring_level import ScoringLevel
from app.models.scoring_scale import ScoringScale
from app.models.user import User
from app.services.security import hash_password

MIN_PASSWORD_LENGTH = 12

AXES = [
    ("Stratégie", "Vision, positionnement et objectifs de l'entreprise."),
    ("Performance", "Organisation, performance opérationnelle et amélioration continue."),
    ("Marketing", "Client, marché, offre et communication."),
    ("RH", "Ressources humaines, compétences et organisation interne."),
    ("Digitalisation", "Outils numériques, données et maturité digitale."),
    ("RSE", "Responsabilité sociétale et environnementale."),
]

# Maturity scale 0-5, used by every axis except RSE.
MATURITY_LEVELS = [
    ("0", 0, "NA", "Non applicable."),
    ("1", 1, "Inexistant", "La pratique n'existe pas dans l'entreprise."),
    ("2", 2, "Informel", "La pratique existe de manière informelle, non structurée ou non documentée."),
    ("3", 3, "En place mais partiel", "La pratique est en place mais reste partielle, irrégulière ou incomplète."),
    ("4", 4, "Structuré", "La pratique est structurée, suivie et appliquée de manière régulière."),
    ("5", 5, "Optimisé et piloté", "La pratique est optimisée, pilotée avec des indicateurs et améliorée dans le temps."),
]

# RSE counts how many statements the company meets (0-3), with "SO" for not applicable.
RSE_LEVELS = [
    ("SO", None, "Sans objet", "Enjeu considéré comme non pertinent pour l'entreprise."),
    ("0", 0, "Aucune affirmation", "L'entreprise ne répond à aucune affirmation."),
    ("1", 1, "Une affirmation", "L'entreprise répond à une des affirmations."),
    ("2", 2, "Deux affirmations", "L'entreprise répond à deux des affirmations."),
    ("3", 3, "Trois affirmations", "L'entreprise répond à trois des affirmations."),
]


def create_axes_and_scales(db):
    """Create missing axes and their scoring scale. Returns how many rows were added."""
    added = {"axes": 0, "scoring_scales": 0, "scoring_levels": 0}
    for order_index, (name, description) in enumerate(AXES, start=1):
        axis = db.query(Axis).filter(Axis.name == name).first()
        if axis is None:
            axis = Axis(name=name, description=description, order_index=order_index, is_active=True)
            db.add(axis)
            db.flush()
            added["axes"] += 1

        scale = db.query(ScoringScale).filter(ScoringScale.axis_id == axis.id).first()
        if scale is None:
            is_rse = name == "RSE"
            scale = ScoringScale(
                axis_id=axis.id,
                name="Échelle RSE SO / 0-3" if is_rse else f"Échelle maturité 0-5 - {name}",
                description="Échelle spécifique RSE avec option Sans Objet." if is_rse else "Échelle de maturité de 0 à 5.",
                max_score=3 if is_rse else 5,
                is_active=True,
            )
            db.add(scale)
            db.flush()
            added["scoring_scales"] += 1

        levels = RSE_LEVELS if name == "RSE" else MATURITY_LEVELS
        existing_codes = {level.code for level in db.query(ScoringLevel).filter(ScoringLevel.scoring_scale_id == scale.id)}
        for order, (code, value, label, description) in enumerate(levels):
            if code not in existing_codes:
                db.add(ScoringLevel(scoring_scale_id=scale.id, code=code, score_value=value,
                                    label=label, description=description, order_index=order))
                added["scoring_levels"] += 1
    return added


def create_first_admin(db, username, password):
    """Create the admin account if it does not exist yet. Returns True when created."""
    if db.query(User).filter(User.username == username).first():
        return False
    if len(password or "") < MIN_PASSWORD_LENGTH:
        raise ValueError(f"ADMIN_PASSWORD must be at least {MIN_PASSWORD_LENGTH} characters long.")
    db.add(User(full_name="Administrateur UIMM", username=username,
                hashed_password=hash_password(password), role="admin", is_active=True))
    return True


def main():
    username = os.getenv("ADMIN_USERNAME")
    password = os.getenv("ADMIN_PASSWORD")
    if not username or not password:
        sys.exit("Set ADMIN_USERNAME and ADMIN_PASSWORD before running this script.")

    Base.metadata.create_all(bind=engine)
    try:
        with SessionLocal.begin() as db:  # one transaction: everything is saved, or nothing
            added = create_axes_and_scales(db)
            admin_created = create_first_admin(db, username, password)
    except ValueError as error:
        sys.exit(f"Nothing was saved: {error}")

    print(f"Axes added: {added['axes']}, scoring scales added: {added['scoring_scales']}, "
          f"scoring levels added: {added['scoring_levels']}")
    print(f"Admin '{username}': {'created' if admin_created else 'already exists, unchanged'}")


if __name__ == "__main__":
    main()
