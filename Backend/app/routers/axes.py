from fastapi import APIRouter, HTTPException, Depends #api router grouping routes together #Depends(get_db) → gives the route access to PostgreSQL
from sqlalchemy.orm import Session
from app.database import get_db

from app.models.axis import Axis #axis read data returned by API
from app.models.question import Question #question read data returned by API
from app.models.scoring_level import ScoringLevel
from app.models.scoring_scale import ScoringScale

from app.schemas.scoring import ScoringScaleRead
from app.schemas.axis import AxisRead
from app.schemas.question import QuestionRead

router = APIRouter(
    prefix="/axes",
    tags=["Axes"]
)


fake_axes = [
    {
        "id": 1,
        "name": "Stratégie",
        "description": "Vision, positionnement et objectifs de l'entreprise.",
        "order_index": 1,
        "is_active": True
    },
    {
        "id": 2,
        "name": "Performance",
        "description": "Organisation, performance opérationnelle et amélioration continue.",
        "order_index": 2,
        "is_active": True
    },
    {
        "id": 3,
        "name": "Marketing",
        "description": "Client, marché, offre et communication.",
        "order_index": 3,
        "is_active": True
    },
    {
        "id": 4,
        "name": "RH",
        "description": "Ressources humaines, compétences et organisation interne.",
        "order_index": 4,
        "is_active": True
    },
    {
        "id": 5,
        "name": "Finance",
        "description": "Pilotage financier et indicateurs économiques.",
        "order_index": 5,
        "is_active": True
    },
    {
        "id": 6,
        "name": "Digitalisation",
        "description": "Outils numériques, données et maturité digitale.",
        "order_index": 6,
        "is_active": True
    },
    {
        "id": 7,
        "name": "RSE",
        "description": "Responsabilité sociétale et environnementale.",
        "order_index": 7,
        "is_active": True
    }
]


fake_questions = [
    {
        "id": 1,
        "axis_id": 1,
        "question_text": "L'entreprise a-t-elle une stratégie clairement définie ?",
        "question_type": "score",
        "max_score": 5,
        "order_index": 1,
        "is_active": True,
        "theme": "Vision stratégique",
        "low_score_meaning": "Manque de vision claire, difficulté à prioriser les actions.",
        "high_score_meaning": "Vision claire, objectifs structurés et meilleure capacité de pilotage.",
        "opportunity_hint": "Formaliser une feuille de route stratégique partagée.",
        "threat_hint": "Risque de dispersion des efforts et de décisions court terme."
    },
    {
        "id": 2,
        "axis_id": 1,
        "question_text": "Les objectifs stratégiques sont-ils partagés avec les équipes ?",
        "question_type": "score",
        "max_score": 5,
        "order_index": 2,
        "is_active": True,
        "theme": "Alignement des équipes",
        "low_score_meaning": "Les équipes peuvent manquer de visibilité sur les priorités.",
        "high_score_meaning": "Les équipes comprennent les objectifs et peuvent contribuer plus efficacement.",
        "opportunity_hint": "Renforcer la communication interne autour des objectifs.",
        "threat_hint": "Risque de désalignement entre direction et terrain."
    },
    {
        "id": 3,
        "axis_id": 6,
        "question_text": "L'entreprise utilise-t-elle des outils numériques pour suivre son activité ?",
        "question_type": "score",
        "max_score": 4,
        "order_index": 1,
        "is_active": True,
        "theme": "Outils numériques",
        "low_score_meaning": "Suivi manuel ou dispersé, manque de fiabilité dans les données.",
        "high_score_meaning": "Outils structurés permettant un meilleur pilotage de l'activité.",
        "opportunity_hint": "Mettre en place des outils simples de suivi et de centralisation.",
        "threat_hint": "Risque d'erreurs, de perte d'information et de dépendance aux fichiers manuels."
    },
    {
        "id": 4,
        "axis_id": 6,
        "question_text": "Les données sont-elles centralisées et exploitables ?",
        "question_type": "score",
        "max_score": 4,
        "order_index": 2,
        "is_active": True,
        "theme": "Données et pilotage",
        "low_score_meaning": "Données dispersées, difficilement exploitables pour la décision.",
        "high_score_meaning": "Données centralisées, exploitables et utiles au pilotage.",
        "opportunity_hint": "Structurer une base de données ou un outil de pilotage centralisé.",
        "threat_hint": "Risque de décisions prises sur des informations incomplètes."
    },
    {
        "id": 5,
        "axis_id": 7,
        "question_text": "L'entreprise a-t-elle identifié ses enjeux RSE prioritaires ?",
        "question_type": "score",
        "max_score": 3,
        "order_index": 1,
        "is_active": True,
        "theme": "Priorités RSE",
        "low_score_meaning": "Les enjeux RSE ne sont pas encore clairement identifiés.",
        "high_score_meaning": "Les priorités RSE sont connues et peuvent être intégrées à la stratégie.",
        "opportunity_hint": "Construire une première feuille de route RSE adaptée à l'entreprise.",
        "threat_hint": "Risque de retard face aux attentes clients, réglementaires ou environnementales."
    }
]


@router.get("/", response_model=list[AxisRead])
def get_axes():
    return fake_axes


@router.get("/{axis_id}/questions", response_model=list[QuestionRead])
def get_questions_by_axis(axis_id: int, db: Session = Depends(get_db)):
    axis = db.query(Axis).filter(Axis.id == axis_id).first()

    if axis is None:
        raise HTTPException(
            status_code=404,
            detail="Axis not found"
        )

    questions = (
        db.query(Question)
        .filter(
            Question.axis_id == axis_id,
            Question.is_active == True
        )
        .order_by(Question.order_index)
        .all()
    )

    return questions

@router.get("/{axis_id}/scoring-scales", response_model=ScoringScaleRead)
def get_scoring_scales_by_axis(axis_id: int, db: Session = Depends(get_db)):
    axis = db.query(Axis).filter(Axis.id == axis_id).first()

    if axis is None:
        raise HTTPException(
            status_code=404,
            detail="Axis not found"
        )
    scoring_scales = (
        db.query(ScoringScale)
        .filter(
            ScoringScale.axis_id == axis_id,
            ScoringScale.is_active == True
        )
        .first()
    )
  

    if scoring_scales is None:
        raise HTTPException(
            status_code=404,
            detail="No scoring scales found for this axis"
        )

    levels = (
        db.query(ScoringLevel)
        .filter(ScoringLevel.scoring_scale_id == scoring_scales.id)
        .order_by(ScoringLevel.order_index)
        .all()
    )
    return {
        "id": scoring_scales.id,
        "axis_id": scoring_scales.axis_id,
        "name": scoring_scales.name,
        "description": scoring_scales.description,
        "max_score": scoring_scales.max_score,
        "is_active": scoring_scales.is_active,
        "levels": levels
    }