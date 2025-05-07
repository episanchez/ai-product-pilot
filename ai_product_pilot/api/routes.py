import json
import uuid
from typing import List, Optional, Union

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from ai_product_pilot.models.backlog import StoryResponse, StoryCreate
from ai_product_pilot.models.feedback import FeedbackResponse
from ai_product_pilot.services.vector_store import VectorStoreService
from ai_product_pilot.lib.supabase import get_supabase_client

router = APIRouter()
vector_store = VectorStoreService()

@router.get("/backlog", response_model=List[StoryResponse])
async def get_backlog(
    min_score: Optional[float] = None,
    theme: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    """
    Récupérer le backlog des user stories générées
    """
    supabase = get_supabase_client()
    query = supabase.table("stories").select("*").order("rice_score", desc=True)
    
    if min_score is not None:
        query = query.gte("rice_score", min_score)
    
    if theme is not None:
        query = query.ilike("themes", f"%{theme}%")
    
    result = query.range(offset, offset + limit - 1).execute()
    return result.data


@router.get("/backlog/{story_id}", response_model=StoryResponse)
async def get_story(story_id: str):
    """
    Récupérer une user story spécifique
    """
    supabase = get_supabase_client()
    result = supabase.table("stories").select("*").eq("id", story_id).execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User story avec ID {story_id} non trouvée",
        )
    
    return result.data[0]


@router.post("/backlog", response_model=StoryResponse, status_code=status.HTTP_201_CREATED)
async def create_story(story: StoryCreate):
    """
    Créer manuellement une user story
    """
    supabase = get_supabase_client()
    
    # Génération d'un ID unique
    story_id = str(uuid.uuid4())
    
    # Préparation des données
    story_data = {
        "id": story_id,
        **story.model_dump(),
        "status": "manual",
    }
    
    # Insertion dans la table stories
    result = supabase.table("stories").insert(story_data).execute()
    
    if hasattr(result, "error") and result.error is not None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création de la story: {result.error.message}",
        )
    
    return {**story_data}


@router.get("/themes", response_model=List[str])
async def get_themes():
    """
    Récupérer la liste des thèmes extraits des feedbacks
    """
    supabase = get_supabase_client()
    
    # Requête SQL personnalisée pour extraire les thèmes uniques
    result = supabase.rpc(
        "get_unique_themes",
    ).execute()
    
    if hasattr(result, "error") and result.error is not None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des thèmes: {result.error.message}",
        )
    
    return result.data


@router.get("/search", response_model=List[Union[FeedbackResponse, StoryResponse]])
async def semantic_search(
    query: str,
    limit: int = 10,
    type: Optional[str] = None
):
    """
    Recherche sémantique dans les documents vectorisés
    """
    results = await vector_store.search(query, limit=limit, filter_type=type)
    return results