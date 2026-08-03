from app.database import SessionLocal
from app.models.axis import Axis
from app.models.scoring_scale import ScoringScale
from app.models.scoring_level import ScoringLevel


def seed_scoring():
    db = SessionLocal()

    maturity_axes = [
        "Stratégie",
        "Performance",
        "Digitalisation",
        "Marketing",
        "RH",
    ]

    maturity_levels = [
        {
            "code": "0",
            "score_value": 0,
            "label": "NA",
            "description": "Non applicable.",
            "order_index": 0,
        },
        {
            "code": "1",
            "score_value": 1,
            "label": "Inexistant",
            "description": "La pratique n'existe pas dans l'entreprise.",
            "order_index": 1,
        },
        {
            "code": "2",
            "score_value": 2,
            "label": "Informel",
            "description": "La pratique existe de manière informelle, non structurée ou non documentée.",
            "order_index": 2,
        },
        {
            "code": "3",
            "score_value": 3,
            "label": "En place mais partiel",
            "description": "La pratique est en place mais reste partielle, irrégulière ou incomplète.",
            "order_index": 3,
        },
        {
            "code": "4",
            "score_value": 4,
            "label": "Structuré",
            "description": "La pratique est structurée, suivie et appliquée de manière régulière.",
            "order_index": 4,
        },
        {
            "code": "5",
            "score_value": 5,
            "label": "Optimisé et piloté",
            "description": "La pratique est optimisée, pilotée avec des indicateurs et améliorée dans le temps.",
            "order_index": 5,
        },
    ]

    rse_levels = [
        {
            "code": "SO",
            "score_value": None,
            "label": "Sans objet",
            "description": "Enjeu considéré comme non pertinent pour l'entreprise.",
            "order_index": 0,
        },
        {
            "code": "0",
            "score_value": 0,
            "label": "Aucune affirmation",
            "description": "L'entreprise ne répond à aucune affirmation.",
            "order_index": 1,
        },
        {
            "code": "1",
            "score_value": 1,
            "label": "Une affirmation",
            "description": "L'entreprise répond à une des affirmations.",
            "order_index": 2,
        },
        {
            "code": "2",
            "score_value": 2,
            "label": "Deux affirmations",
            "description": "L'entreprise répond à deux des affirmations.",
            "order_index": 3,
        },
        {
            "code": "3",
            "score_value": 3,
            "label": "Trois affirmations",
            "description": "L'entreprise répond à trois des affirmations.",
            "order_index": 4,
        },
    ]

    for axis_name in maturity_axes:
        axis = db.query(Axis).filter(Axis.name == axis_name).first()

        if axis is None:
            print(f"Axis not found: {axis_name}")
            continue

        scale_name = f"Échelle maturité 0-5 - {axis_name}"

        scale = (
            db.query(ScoringScale)
            .filter(ScoringScale.axis_id == axis.id)
            .first()
        )

        if scale is None:
            scale = ScoringScale(
                axis_id=axis.id,
                name=scale_name,
                description="Échelle de maturité de 0 à 5.",
                max_score=5,
                is_active=True,
            )
            db.add(scale)
            db.commit()
            db.refresh(scale)

        for level_data in maturity_levels:
            existing_level = (
                db.query(ScoringLevel)
                .filter(
                    ScoringLevel.scoring_scale_id == scale.id,
                    ScoringLevel.code == level_data["code"],
                )
                .first()
            )

            if existing_level is None:
                level = ScoringLevel(
                    scoring_scale_id=scale.id,
                    code=level_data["code"],
                    score_value=level_data["score_value"],
                    label=level_data["label"],
                    description=level_data["description"],
                    order_index=level_data["order_index"],
                )
                db.add(level)

    rse_axis = db.query(Axis).filter(Axis.name == "RSE").first()

    if rse_axis is None:
        print("Axis not found: RSE")
    else:
        rse_scale = (
            db.query(ScoringScale)
            .filter(ScoringScale.axis_id == rse_axis.id)
            .first()
        )

        if rse_scale is None:
            rse_scale = ScoringScale(
                axis_id=rse_axis.id,
                name="Échelle RSE SO / 0-3",
                description="Échelle spécifique RSE avec option Sans Objet.",
                max_score=3,
                is_active=True,
            )
            db.add(rse_scale)
            db.commit()
            db.refresh(rse_scale)

        for level_data in rse_levels:
            existing_level = (
                db.query(ScoringLevel)
                .filter(
                    ScoringLevel.scoring_scale_id == rse_scale.id,
                    ScoringLevel.code == level_data["code"],
                )
                .first()
            )

            if existing_level is None:
                level = ScoringLevel(
                    scoring_scale_id=rse_scale.id,
                    code=level_data["code"],
                    score_value=level_data["score_value"],
                    label=level_data["label"],
                    description=level_data["description"],
                    order_index=level_data["order_index"],
                )
                db.add(level)

    db.commit()
    db.close()

    print("Scoring scales and levels inserted successfully.")


if __name__ == "__main__":
    seed_scoring()