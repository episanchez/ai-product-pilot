from typing import Dict, List, TypedDict, Annotated, Any
from langgraph.graph import StateGraph, END
import asyncio

from app.langgraph.nodes.ingest import ingest_feedback
from app.langgraph.nodes.extract import extract_insights
from app.langgraph.nodes.synthesize import synthesize_insights
from app.langgraph.nodes.generate import generate_stories
from app.langgraph.nodes.prioritize import prioritize_stories


# Définition du type d'état
class FeedbackState(TypedDict):
    feedback_id: str  # ID du feedback en cours de traitement
    feedback_data: Dict[str, Any]  # Données brutes du feedback
    docs: List[Dict[str, Any]]  # Documents vectorisés
    entities: Dict[str, Any]  # Entités extraites (thèmes, sentiments, etc.)
    summary: str  # Résumé des insights
    stories: List[Dict[str, Any]]  # User stories générées


# Construction du graphe de traitement
def build_feedback_graph() -> StateGraph:
    # Initialisation du graphe
    graph = StateGraph(FeedbackState)
    
    # Ajout des nœuds
    graph.add_node("ingest", ingest_feedback)
    graph.add_node("extract", extract_insights)
    graph.add_node("synthesize", synthesize_insights)
    graph.add_node("generate", generate_stories)
    graph.add_node("prioritize", prioritize_stories)
    
    # Définition du flux de traitement
    graph.add_edge("ingest", "extract")
    graph.add_edge("extract", "synthesize")
    graph.add_edge("synthesize", "generate")
    graph.add_edge("generate", "prioritize")
    graph.add_edge("prioritize", END)
    
    # Définition du point d'entrée
    graph.set_entry_point("ingest")
    
    return graph


# Création du graphe
feedback_processing_graph = build_feedback_graph().compile()