import datetime
from typing import Optional
from pydantic import BaseModel, Field, List

class StoryBase(BaseModel):
    title: str = Field(description="Titre concis de la user story")
    as_a: str = Field(description="Type d'utilisateur concerné")
    i_want: str = Field(description="Ce que l'utilisateur souhaite accomplir")
    so_that: str = Field(description="Le bénéfice attendu")
    description: str = Field(description="Description détaillée de la user story")
    acceptance_criteria: List[str] = Field(description="Critères d'acceptation")
    themes: List[str] = Field(description="Thèmes associés à cette story")
    

class StoryCreate(StoryBase):
    reach: float = Field(..., ge=0, le=10)
    impact: float = Field(..., ge=0, le=3)
    confidence: float = Field(..., ge=0, le=10)
    effort: float = Field(..., ge=0.1, le=10)
    rice_score: Optional[float] = None


class StoryResponse(StoryBase):
    id: str
    reach: float
    impact: float
    confidence: float
    effort: float
    rice_score: float
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Modèle pour la liste de user stories
class UserStories(BaseModel):
    stories: List[StoryBase] = Field(description="Liste des user stories générées")