from app.database import SessionLocal
from app.models.axis import Axis
from app.models.question import Question


def seed_questions():
    db = SessionLocal()

    questions_data = [
        {
            "axis_name": "Stratégie",
            "question_text": "L'entreprise a-t-elle une stratégie clairement définie ?",
            "question_type": "score",
            "max_score": 5,
            "order_index": 1,
            "theme": "Vision stratégique",
            "low_score_meaning": "Manque de vision claire, difficulté à prioriser les actions.",
            "high_score_meaning": "Vision claire, objectifs structurés et meilleure capacité de pilotage.",
            "opportunity_hint": "Formaliser une feuille de route stratégique partagée.",
            "threat_hint": "Risque de dispersion des efforts et de décisions court terme.",
        },
        {
            "axis_name": "Stratégie",
            "question_text": "Les objectifs stratégiques sont-ils partagés avec les équipes ?",
            "question_type": "score",
            "max_score": 5,
            "order_index": 2,
            "theme": "Alignement des équipes",
            "low_score_meaning": "Les équipes peuvent manquer de visibilité sur les priorités.",
            "high_score_meaning": "Les équipes comprennent les objectifs et peuvent contribuer plus efficacement.",
            "opportunity_hint": "Renforcer la communication interne autour des objectifs.",
            "threat_hint": "Risque de désalignement entre direction et terrain.",
        },
        {
            "axis_name": "Digitalisation",
            "question_text": "L'entreprise utilise-t-elle des outils numériques pour suivre son activité ?",
            "question_type": "score",
            "max_score": 4,
            "order_index": 1,
            "theme": "Outils numériques",
            "low_score_meaning": "Suivi manuel ou dispersé, manque de fiabilité dans les données.",
            "high_score_meaning": "Outils structurés permettant un meilleur pilotage de l'activité.",
            "opportunity_hint": "Mettre en place des outils simples de suivi et de centralisation.",
            "threat_hint": "Risque d'erreurs, de perte d'information et de dépendance aux fichiers manuels.",
        },
        {
            "axis_name": "Digitalisation",
            "question_text": "Les données sont-elles centralisées et exploitables ?",
            "question_type": "score",
            "max_score": 4,
            "order_index": 2,
            "theme": "Données et pilotage",
            "low_score_meaning": "Données dispersées, difficilement exploitables pour la décision.",
            "high_score_meaning": "Données centralisées, exploitables et utiles au pilotage.",
            "opportunity_hint": "Structurer une base de données ou un outil de pilotage centralisé.",
            "threat_hint": "Risque de décisions prises sur des informations incomplètes.",
        },
        {
            "axis_name": "RSE",
            "question_text": "L'entreprise a-t-elle identifié ses enjeux RSE prioritaires ?",
            "question_type": "score",
            "max_score": 3,
            "order_index": 1,
            "theme": "Priorités RSE",
            "low_score_meaning": "Les enjeux RSE ne sont pas encore clairement identifiés.",
            "high_score_meaning": "Les priorités RSE sont connues et peuvent être intégrées à la stratégie.",
            "opportunity_hint": "Construire une première feuille de route RSE adaptée à l'entreprise.",
            "threat_hint": "Risque de retard face aux attentes clients, réglementaires ou environnementales.",
        },
    ]

    for question_data in questions_data:
        axis = db.query(Axis).filter(Axis.name == question_data["axis_name"]).first()

        if axis is None:
            print(f"Axis not found: {question_data['axis_name']}")
            continue

        existing_question = (
            db.query(Question)
            .filter(Question.question_text == question_data["question_text"])
            .first()
        )

        if existing_question is None:
            new_question = Question(
                axis_id=axis.id,
                question_text=question_data["question_text"],
                question_type=question_data["question_type"],
                max_score=question_data["max_score"],
                order_index=question_data["order_index"],
                is_active=True,
                theme=question_data["theme"],
                low_score_meaning=question_data["low_score_meaning"],
                high_score_meaning=question_data["high_score_meaning"],
                opportunity_hint=question_data["opportunity_hint"],
                threat_hint=question_data["threat_hint"],
            )
            db.add(new_question)

    db.commit()
    db.close()

    print("Questions inserted successfully.")


if __name__ == "__main__":
    seed_questions()