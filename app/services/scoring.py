from typing import Dict, List, Tuple, Any

def calculate_rice_score(
    reach: float,
    impact: float,
    confidence: float,
    effort: float
) -> float:
    """
    Calcule le score RICE (Reach, Impact, Confidence, Effort)
    
    Args:
        reach: Estimation du nombre d'utilisateurs affectés (0-10)
        impact: Impact sur ces utilisateurs (0-10)
        confidence: Niveau de confiance dans l'estimation (0-10)
        effort: Estimation de l'effort de développement (0.1-10)
        
    Returns:
        Score RICE calculé
    """
    # Normalisation des valeurs
    normalized_reach = max(0, min(reach, 10))
    normalized_impact = max(0, min(impact, 10))
    normalized_confidence = max(0, min(confidence, 10)) / 10  # Convertir en pourcentage (0-1)
    normalized_effort = max(0.1, min(effort, 10))  # Éviter la division par zéro
    
    # Calcul du score RICE
    rice_score = (normalized_reach * normalized_impact * normalized_confidence) / normalized_effort
    
    return round(rice_score, 2)


def prioritize_stories(stories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Priorise une liste de user stories en fonction de leur score RICE
    
    Args:
        stories: Liste de dictionnaires représentant les user stories
        
    Returns:
        Liste tri       Liste triée des stories par score RICE décroissant
    """
    # Calculer le score RICE pour chaque story qui n'en a pas déjà un
    for story in stories:
        if "rice_score" not in story or story["rice_score"] is None:
            story["rice_score"] = calculate_rice_score(
                story["reach"],
                story["impact"],
                story["confidence"],
                story["effort"]
            )
    
    # Trier les stories par score RICE décroissant
    sorted_stories = sorted(stories, key=lambda x: x["rice_score"], reverse=True)
    
    return sorted_stories


def estimate_rice_parameters(
    story_text: str,
    theme_importance: Dict[str, float],
    sentiment_score: float,
    user_count: int
) -> Tuple[float, float, float, float]:
    """
    Estime les paramètres RICE à partir des données disponibles
    
    Args:
        story_text: Texte de la user story
        theme_importance: Dictionnaire des thèmes avec leur importance
        sentiment_score: Score de sentiment (-1 à 1)
        user_count: Nombre d'utilisateurs concernés
        
    Returns:
        Tuple (reach, impact, confidence, effort)
    """
    # Estimer la portée (reach) en fonction du nombre d'utilisateurs
    # Normaliser entre 0 et 10
    reach = min(10, max(1, user_count / 100))
    
    # Estimer l'impact en fonction du sentiment
    # Convertir le sentiment de [-1, 1] à [1, 10]
    # Un sentiment négatif fort indique un problème important à résoudre (impact élevé)
    impact = 5.5 - (sentiment_score * 4.5)
    
    # Estimer la confiance en fonction de la cohérence des données
    # Par défaut, on commence avec une confiance moyenne
    confidence = 7.0
    
    # Estimer l'effort (par défaut à 5 = effort moyen)
    effort = 5.0
    
    return reach, impact, confidence, effort