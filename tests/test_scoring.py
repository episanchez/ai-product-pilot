import pytest
from ai_product_pilot.services.scoring import calculate_rice_score, prioritize_stories, estimate_rice_parameters


def test_calculate_rice_score():
    """Test du calcul du score RICE avec différentes valeurs"""
    
    # Test avec des valeurs moyennes
    score = calculate_rice_score(
        reach=5.0,
        impact=5.0,
        confidence=5.0,
        effort=5.0
    )
    assert score == 2.5  # (5 * 5 * 0.5) / 5 = 2.5
    
    # Test avec impact élevé
    score = calculate_rice_score(
        reach=5.0,
        impact=10.0,
        confidence=5.0,
        effort=5.0
    )
    assert score == 5.0  # (5 * 10 * 0.5) / 5 = 5.0
    
    # Test avec effort minimal
    score = calculate_rice_score(
        reach=5.0,
        impact=5.0,
        confidence=5.0,
        effort=0.1
    )
    assert score == 125.0  # (5 * 5 * 0.5) / 0.1 = 125.0
    
    # Test avec des valeurs hors limites (doivent être normalisées)
    score = calculate_rice_score(
        reach=15.0,  # devrait être limité à 10
        impact=5.0,
        confidence=12.0,  # devrait être limité à 10 puis divisé par 10
        effort=0.0  # devrait être augmenté à 0.1
    )
    assert score == 50.0  # (10 * 5 * 1.0) / 0.1 = 50.0


def test_prioritize_stories():
    """Test de la priorisation des stories"""
    
    # Liste de stories à prioriser
    stories = [
        {
            "title": "Story A",
            "reach": 3.0,
            "impact": 2.0,
            "confidence": 9.0,
            "effort": 1.0,
            # rice_score manquant, doit être calculé
        },
        {
            "title": "Story B",
            "reach": 8.0,
            "impact": 7.0,
            "confidence": 6.0,
            "effort": 4.0,
            "rice_score": 8.4  # déjà calculé, ne doit pas changer
        },
        {
            "title": "Story C",
            "reach": 5.0,
            "impact": 9.0,
            "confidence": 7.0,
            "effort": 2.0,
            # rice_score manquant, doit être calculé
        }
    ]
    
    result = prioritize_stories(stories)
    
    # Vérifier que toutes les stories ont un score RICE
    assert all("rice_score" in story for story in result)
    
    # Vérifier que la Story B conserve son score d'origine
    story_b = next(s for s in result if s["title"] == "Story B")
    assert story_b["rice_score"] == 8.4
    
    # Vérifier que les stories sont triées par score décroissant
    assert result[0]["rice_score"] >= result[1]["rice_score"] >= result[2]["rice_score"]


def test_estimate_rice_parameters():
    """Test de l'estimation des paramètres RICE"""
    
    # Cas d'un feedback négatif important sur un thème majeur
    theme_importance = {"performance": 9.5, "ui": 5.0, "pricing": 2.0}
    sentiment_score = -0.8  # sentiment très négatif
    user_count = 500
    
    reach, impact, confidence, effort = estimate_rice_parameters(
        story_text="Les utilisateurs se plaignent de lenteurs importantes",
        theme_importance=theme_importance,
        sentiment_score=sentiment_score,
        user_count=user_count
    )
    
    # La portée devrait être élevée (beaucoup d'utilisateurs)
    assert reach > 5.0
    # L'impact devrait être élevé (sentiment très négatif)
    assert impact > 7.0
    # Les autres paramètres devraient être raisonnables
    assert 1.0 <= confidence <= 10.0
    assert 1.0 <= effort <= 10.0