from typing import Dict, List, Any
import os
import json

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from app.supabase.client import get_supabase_client
from app.core.settings import settings


# Modèle Pydantic pour l'extraction structurée
class ExtractedInsights(BaseModel):
    themes: List[str] = Field(
        description="Liste des thèmes principaux identifiés dans les feedbacks"
    )
    sentiments: Dict[str, float] = Field(
        description="Score de sentiment pour chaque thème (entre -1 et 1)"
    )
    pain_points: List[str] = Field(
        description="Liste des points de douleur identifiés"
    )
    feature_requests: List[str] = Field(
        description="Liste des fonctionnalités demandées ou suggestions"
    )
    user_personas: List[Dict[str, str]] = Field(
        description="Personas utilisateurs identifiés dans les feedbacks"
    )
    key_metrics: Dict[str, Any] = Field(
        description="Métriques clés extraites des feedbacks (si disponibles)"
    )


async def extract_insights(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Nœud qui extrait des insights structurés à partir des documents
    
    Args:
        state: État contenant les documents et les données de feedback
        
    Returns:
        État mis à jour avec les entités extraites
    """
    feedback_id = state["feedback_id"]
    docs = state["docs"]
    
    # Combiner tous les textes des documents
    all_text = "\n\n".join([doc["content"] for doc in docs])
    
    # Limiter la longueur du texte pour éviter les dépassements de contexte
    max_length = 12000
    if len(all_text) > max_length:
        all_text = all_text[:max_length] + "... [texte tronqué]"
    
    # Charger le template de prompt pour l'extraction
    with open(os.path.join(os.path.dirname(__file__), "../../..", "prompts/extract_insights.txt"), "r") as f:
        template = f.read()
    
    # Créer le prompt
    prompt = ChatPromptTemplate.from_template(template)
    
    # Configurer le modèle LLM
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.3,
        openai_api_key=settings.openai_api_key
    )
    
    # Configurer le parser de sortie
    parser = PydanticOutputParser(pydantic_object=ExtractedInsights)
    
    # Chaîne de traitement
    chain = prompt | llm | parser
    
    # Exécuter l'extraction
    insights = await chain.ainvoke({
        "feedback_text": all_text,
        "format_instructions": parser.get_format_instructions()
    })
    
    # Mettre à jour le statut du feedback
    supabase = get_supabase_client()
    supabase.table("feedback").update({
        "status": "analyzed",
        "analysis": json.dumps(insights.model_dump())
    }).eq("id", feedback_id).execute()
    
    # Retourner l'état mis à jour
    return {
        **state,
        "entities": insights.model_dump()
    }