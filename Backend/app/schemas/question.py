from pydantic import BaseModel
from typing import Optional

class QuestionRead(BaseModel):
    id: int 
    axis_id: int    #which axis this question belongs to
    question_text: str #the question
    question_type: str  #score, text, yes_no, etc.
    max_score: Optional[int] = None #example 4 or 5
    order_index: int #display order
    is_active: bool = True  # Default value for is_active
    theme: Optional[str] = None  #optional theme for the question
    low_score_meaning: Optional[str] = None
    high_score_meaning: Optional[str] = None
    opportunity: Optional[str] = None 
    threat: Optional[str] = None