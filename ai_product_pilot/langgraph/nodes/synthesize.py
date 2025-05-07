from typing import Dict, List, Any
import json

from langchain.schema.runnable import Runnable
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from ai_product_pilot.core.settings import settings
from ai_product_pilot.lib.supabase import get_supabase_client


class InsightSynthesizer(Runnable):
    """
    Classe qui synthétise les insights extraits des feedbacks en un résumé cohérent.
    Hérite de Runnable pour être compatible avec LangGraph.
    """
    
    def __init__(self):
        """Initialise le synthesizer avec un modèle LLM et un template de prompt"""
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.4,
            openai_api_key=settings.openai_api_key
        )
        
        self.template = """
        En tant qu'analyste de produit, synthétise les insights extraits des feedbacks utilisateurs en un résumé cohérent et actionnable.
        
        ## Contexte
        - Source du feedback: {feedback_source}
        - Titre: {feedback_title}
        
        ## Thèmes identifiés
        {themes}
        
        ## Sentiments par thème
        {sentiments}
        
        ## Points de douleur
        {pain_points}
        
        ## Fonctionnalités demandées
        {feature_requests}
        
        ## Personas utilisateurs
        {user_personas}
        
        ## Exemples de feedback
        {sample_feedback}
        
        ## Instructions
        1. Synthétise ces données en un résumé de 2-3 paragraphes
        2. Mets en évidence les tendances principales
        3. Identifie les opportunités d'amélioration les plus importantes
        4. Souligne les besoins utilisateurs non satisfaits
        
        ## Synthèse
        """
        
        self.prompt = ChatPromptTemplate.from_template(self.template)
        self.chain = self.prompt | self.llm
    
    async def ainvoke(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Méthode asynchrone pour synthétiser les insights
        
        Args:
            state: État contenant les entités extraites
            
        Returns:
            État mis à jour avec le résumé
        """
        feedback_id = state["feedback_id"]
        entities = state["entities"]
        docs = state["docs"]
        
        # Créer un contexte enrichi pour la synthèse
        context = {
            "themes": entities.get("themes", []),
            "sentiments": entities.get("sentiments", {}),
            "pain_points": entities.get("pain_points", []),
            "feature_requests": entities.get("feature_requests", []),
            "user_personas": entities.get("user_personas", []),
            "sample_feedback": [doc["content"][:200] + "..." for doc in docs[:3]],
            "feedback_source": state["feedback_data"].get("source", "inconnu"),
            "feedback_title": state["feedback_data"].get("title", "")
        }
        
        # Exécuter la synthèse
        result = await self.chain.ainvoke(context)
        summary = result.content
        
        # Mettre à jour le feedback avec la synthèse
        supabase = get_supabase_client()
        supabase.table("feedback").update({
            "summary": summary
        }).eq("id", feedback_id).execute()
        
        # Retourner l'état mis à jour
        return {
            **state,
            "summary": summary
        }
    
    def invoke(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Méthode synchrone pour synthétiser les insights
        
        Args:
            state: État contenant les entités extraites
            
        Returns:
            État mis à jour avec le résumé
        """
        import asyncio
        
        # Appeler la version asynchrone dans un event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # Si nous ne sommes pas dans un event loop, en créer un nouveau
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.ainvoke(state))


# Pour maintenir la compatibilité avec le code existant
synthesize_insights = InsightSynthesizer()