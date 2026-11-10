from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
# from typing import Any  # Utilisé uniquement par les schémas commentés.


# schema not used in current routes, retained for reference.
# class SWOTAxisScoreContext(BaseModel):
#     axis_id: int
#     axis_name: str
#     score_total: int
#     score_max: int
#     percentage: float
#     answered_questions: int


# schema not used in current routes, retained for reference.
# class SWOTQuestionContext(BaseModel):
#     axis_id: int
#     axis_name: str
#     question_id: int
#     question_text: str
#
#     score_code: Optional[str] = None
#     score_value: Optional[int] = None
#     score_label: Optional[str] = None
#     score_description: Optional[str] = None
#
#     max_score: Optional[int] = None
#     answer_text: Optional[str] = None
#     comment: Optional[str] = None
#
#     theme: Optional[str] = None
#     low_score_meaning: Optional[str] = None
#     high_score_meaning: Optional[str] = None
#     opportunity_hint: Optional[str] = None
#     threat_hint: Optional[str] = None


# Schéma inutilisé dans les routes actuelles, conservé pour référence.
# class SWOTContextRead(BaseModel):
#     company: dict[str, Any]
#     selected_axes: list[dict[str, Any]]
#     axis_scores: list[dict[str, Any]]  # Ancien schéma SWOTAxisScoreContext désactivé.
#     company_profile: list[dict[str, Any]]
#     diagnostic_answers: list[dict[str, Any]]
#     swot_evidence: dict[str, list[dict[str, Any]]]


class SWOTCreate(BaseModel):
    axis_id: Optional[int] = None

    strengths: Optional[str] = None
    weaknesses: Optional[str] = None
    opportunities: Optional[str] = None
    threats: Optional[str] = None

    generation_source: str = "manual"
    generated_by_ai: bool = False
    ai_model: Optional[str] = None
    status: str = "draft"

class SWOTRead(BaseModel):
    id: int
    company_id: int
    axis_id: Optional[int] = None

    strengths: Optional[str] = None
    weaknesses: Optional[str] = None
    opportunities: Optional[str] = None
    threats: Optional[str] = None

    generation_source: str
    generated_by_ai: bool
    ai_model: Optional[str] = None
    status: str

    created_by_user_id: Optional[int] = None
    validated_by_user_id: Optional[int] = None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SWOTUpdate(BaseModel):
    strengths: Optional[str] = None
    weaknesses: Optional[str] = None
    opportunities: Optional[str] = None
    threats: Optional[str] = None

    status: Optional[str] = None