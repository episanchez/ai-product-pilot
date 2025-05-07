from typing import Dict, List, Any
import os
import json

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field, field_validator
from ai_product_pilot.core.settings import settings
from ai_product_pilot.models.backlog import UserStories
from ai_product_pilot.lib.supabase import get_supabase_client


async def generate_stories(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Nœud qui génère des user stories basées sur les insights et la synthèse
    
    Args:
        state: État contenant la synthèse et les entités
        
    Returns:
        État mis à jour avec les user stories générées
    """
    feedback_id = state["feedback_id"]
    summary = state["summary"]
    entities = state["entities"]
    
    # Charger le template de prompt
    with open(os.path.join(os.path.dirname(__file__), "../../..", "prompts/generate_stories.txt"), "r") as f:
        template = f.read()
    
    # Créer le contexte pour la génération
    context = {
        "summary": summary,
        "themes": entities.get("themes", []),
        "pain_points": entities.get("pain_points", []),
        "feature_requests": entities.get("feature_requests", []),
        "user_personas": entities.get("user_personas", []),
        "sentiments": entities.get("sentiments", {}),
    }
    
    # Configurer le prompt
    prompt = ChatPromptTemplate.from_template(template)
    
    # Configurer le LLM
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.5,
        openai_api_key=settings.openai_api_key
    )
    
    # Configurer le parser
    parser = PydanticOutputParser(pydantic_object=UserStories)
    
    # Chaîne de traitement
    chain = prompt | llm | parser
    
    # Exécuter la génération
    result = await chain.ainvoke({
        **context,
        "format_instructions": parser.get_format_instructions()
    })
    
    # Convertir les objets Pydantic en dictionnaires
    stories_dicts = []
    for story in result.stories:
        story_dict = story.model_dump()
        # Ajouter des métadonnées supplémentaires
        story_dict["feedback_ids"] = [feedback_id]
        stories_dicts.append(story_dict)
    
    # Mettre à jour l'état
    return {
        **state,
        "stories": stories_dicts
    }