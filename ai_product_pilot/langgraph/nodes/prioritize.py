from typing import Dict, List, Any
import json
import uuid

from ai_product_pilot.services.scoring import calculate_rice_score, estimate_rice_parameters
from ai_product_pilot.lib.supabase import get_supabase_client
from ai_product_pilot.services.vector_store import VectorStoreService


async def prioritize_stories(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Nœud qui attribue des priorités aux user stories et les sauvegarde
    
    Args:
        state: État contenant les user stories générées
        
    Returns:
        État mis à jour avec les stories priorisées
    """
    feedback_id = state["feedback_id"]
    stories = state["stories"]
    entities = state["entities"]
    
    # Client Supabase
    supabase = get_supabase_client()
    vector_store = VectorStoreService()
    
    # Données pour l'estimation RICE
    theme_importance = {}
    sentiment_scores = entities.get("sentiments", {})
    
    # Calculer l'importance des thèmes en fonction de leur fréquence d'apparition
    all_themes = entities.get("themes", [])
    for theme in all_themes:
        theme_importance[theme] = all_themes.count(theme) / len(all_themes) * 10
    
    # Estimer les paramètres RICE pour chaque story
    prioritized_stories = []
    for story in stories:
        # Estimer la portée, l'impact, la confiance et l'effort
        # La portée est basée sur les personas et les thèmes
        user_count = len(entities.get("user_personas", [])) * 100  # estimation
        
        # Calculer le sentiment moyen pour les thèmes associés à cette story
        relevant_sentiments = [
            sentiment_scores.get(theme, 0) 
            for theme in story["themes"] 
            if theme in sentiment_scores
        ]
        avg_sentiment = sum(relevant_sentiments) / len(relevant_sentiments) if relevant_sentiments else 0
        
        # Estimer les paramètres RICE
        reach, impact, confidence, effort = estimate_rice_parameters(
            story_text=story["description"],
            theme_importance=theme_importance,
            sentiment_score=avg_sentiment,
            user_count=user_count
        )
        
        # Calculer le score RICE
        rice_score = calculate_rice_score(reach, impact, confidence, effort)
        
        # Créer l'objet story enrichi
        story_id = str(uuid.uuid4())
        prioritized_story = {
            "id": story_id,
            **story,
            "reach": reach,
            "impact": impact,
            "confidence": confidence,
            "effort": effort,
            "rice_score": rice_score,
            "status": "generated"
        }
        
        # Ajouter à la liste des stories priorisées
        prioritized_stories.append(prioritized_story)
        
        # Insérer dans la base de données
        supabase.table("stories").insert(prioritized_story).execute()
        
        # Vectoriser la story pour permettre la recherche sémantique
        story_content = f"Title: {story['title']}\nAs a {story['as_a']}, I want {story['i_want']} so that {story['so_that']}\n\n{story['description']}"
        story_metadata = {
            "id": story_id,
            "title": story["title"],
            "themes": story["themes"],
            "rice_score": rice_score,
            "type": "story",
            "feedback_ids": story["feedback_ids"]
        }
        
        # Ajouter au vector store
        await vector_store.add_documents(
            texts=[story_content],
            metadatas=[story_metadata],
            namespace=f"story:{story_id}"
        )
    
    # Trier les stories par score RICE
    prioritized_stories.sort(key=lambda x: x["rice_score"], reverse=True)
    
    # Mettre à jour le statut du feedback
    supabase.table("feedback").update({
        "status": "completed",
        "stories_count": len(prioritized_stories)
    }).eq("id", feedback_id).execute()
    
    # Retourner l'état mis à jour
    return {
        **state,
        "stories": prioritized_stories
    }