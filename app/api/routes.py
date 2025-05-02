import json
import uuid
from typing import Dict, List, Optional, Union

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse

from app.models.backlog import StoryResponse, StoryCreate
from app.models.feedback import FeedbackResponse, FeedbackCreate
from app.services.vector_store import VectorStoreService
from app.supabase.client import get_supabase_client
from app.langgraph.graph import feedback_processing_graph

router = APIRouter()
vector_store = VectorStoreService()


@router.post("/feedback/upload", response_model=FeedbackResponse)
async def upload_feedback(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    source: str = Form(...),
    file: Optional[UploadFile] = File(None),
    content: Optional[str] = Form(None),
):
    """
    Endpoint pour télécharger un feedback utilisateur sous forme de fichier ou de texte
    """
    if not file and not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Veuillez fournir soit un fichier, soit du contenu textuel",
        )
    
    # Génération d'un ID unique pour ce feedback
    feedback_id = str(uuid.uuid4())
    
    # Client Supabase
    supabase = get_supabase_client()
    
    # Si un fichier est fourni, le stocker dans Supabase Storage
    file_path = None
    if file:
        # Chemin de stockage dans le bucket
        file_extension = file.filename.split(".")[-1] if file.filename else "txt"
        file_path = f"{feedback_id}.{file_extension}"
        
        # Télécharger dans le bucket "feedback_raw"
        file_content = await file.read()
        res = supabase.storage.from_("feedback_raw").upload(
            path=file_path,
            file=file_content,
        )
        
        if hasattr(res, "error") and res.error is not None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erreur lors de l'upload du fichier: {res.error.message}",
            )
    
    # Créer l'entrée de feedback dans la base de données
    feedback_data = {
        "id": feedback_id,
        "title": title,
        "description": description,
        "source": source,
        "file_path": file_path,
        "content": content,
        "status": "pending",
    }
    
    # Insérer dans la table feedback
    res = supabase.table("feedback").insert(feedback_data).execute()
    
    if hasattr(res, "error") and res.error is not None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'insertion du feedback: {res.error.message}",
        )
    
    return FeedbackResponse(
        id=feedback_id,
        title=title,
        description=description,
        source=source,
        file_path=file_path,
        content=content,
        status="pending",
    )


@router.post("/feedback/process/{feedback_id}", status_code=status.HTTP_202_ACCEPTED)
async def process_feedback(feedback_id: str):
    """
    Endpoint pour déclencher le traitement d'un feedback
    """
    # Vérifier que le feedback existe
    supabase = get_supabase_client()
    result = supabase.table("feedback").select("*").eq("id", feedback_id).execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feedback avec ID {feedback_id} non trouvé",
        )
    
    feedback = result.data[0]
    
    # Mettre à jour le statut du feedback
    supabase.table("feedback").update({"status": "processing"}).eq("id", feedback_id).execute()
    
    try:
        # Exécuter le graphe de traitement de façon asynchrone
        # Dans un vrai projet, ceci serait fait via un worker Celery/RQ
        await feedback_processing_graph.ainvoke({
            "feedback_id": feedback_id,
            "feedback_data": feedback,
            "docs": [],
            "entities": {},
            "summary": "",
            "stories": []
        })
        
        return {"message": f"Traitement du feedback {feedback_id} initié avec succès"}
    
    except Exception as e:
        # En cas d'erreur, mettre à jour le statut
        supabase.table("feedback").update({"status": "error", "error": str(e)}).eq("id", feedback_id).execute()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du traitement: {str(e)}",
        )


@router.get("/feedback", response_model=List[FeedbackResponse])
async def list_feedbacks():
    """
    Récupérer la liste des feedbacks
    """
    supabase = get_supabase_client()
    result = supabase.table("feedback").select("*").order("created_at", desc=True).execute()
    
    return result.data


@router.get("/feedback/{feedback_id}", response_model=FeedbackResponse)
async def get_feedback(feedback_id: str):
    """
    Récupérer un feedback spécifique
    """
    supabase = get_supabase_client()
    result = supabase.table("feedback").select("*").eq("id", feedback_id).execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feedback avec ID {feedback_id} non trouvé",
        )
    
    return result.data[0]


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