from app.database import SessionLocal
from app.models.axis import Axis


def seed_axes():
    db = SessionLocal()

    axes_data = [
        {
            "name": "Stratégie",
            "description": "Vision, positionnement et objectifs de l'entreprise.",
            "order_index": 1,
        },
        {
            "name": "Performance",
            "description": "Organisation, performance opérationnelle et amélioration continue.",
            "order_index": 2,
        },
        {
            "name": "Marketing",
            "description": "Client, marché, offre et communication.",
            "order_index": 3,
        },
        {
            "name": "RH",
            "description": "Ressources humaines, compétences et organisation interne.",
            "order_index": 4,
        },
        {
            "name": "Finance",
            "description": "Pilotage financier et indicateurs économiques.",
            "order_index": 5,
        },
        {
            "name": "Digitalisation",
            "description": "Outils numériques, données et maturité digitale.",
            "order_index": 6,
        },
        {
            "name": "RSE",
            "description": "Responsabilité sociétale et environnementale.",
            "order_index": 7,
        },
    ]

    for axis_data in axes_data:
        existing_axis = db.query(Axis).filter(Axis.name == axis_data["name"]).first() #It checks if the axis already exists. So if you run the script twice, it will not duplicate the axes.

        if existing_axis is None:
            new_axis = Axis(
                name=axis_data["name"],
                description=axis_data["description"],
                order_index=axis_data["order_index"],
                is_active=True,
            )
            db.add(new_axis)

    db.commit()
    db.close()

    print("Axes inserted successfully.")


if __name__ == "__main__":
    seed_axes()