import pytest
import asyncio
from unittest.mock import patch, MagicMock
from ai_product_pilot.langgraph.nodes.prioritize import prioritize_stories


@pytest.mark.asyncio
async def test_prioritize_stories_node():
    """Test du nœud de priorisation des stories"""
    
    # État d'entrée simulé
    input_state = {
        "feedback_id": "test-feedback-id",
        "feedback_data": {
            "id": "test-feedback-id",
            "title": "Test Feedback",
            "source": "test"
        },
        "docs": [],
        "entities": {
            "themes": ["performance", "ui", "pricing"],
            "sentiments": {"performance": -0.7, "ui": 0.5, "pricing": -0.2},
            "user_personas": [{"role": "developer", "needs": "fast compilation"}]
        },
        "summary": "Ce feedback concerne principalement des problèmes de performance",
        "stories": [
            {
                "title": "Améliorer les performances de compilation",
                "as_a": "développeur",
                "i_want": "une compilation plus rapide",
                "so_that": "je puisse itérer plus rapidement",
                "description": "Les utilisateurs signalent des temps de compilation lents",
                "acceptance_criteria": ["Temps de compilation réduit de 50%"],
                "themes": ["performance"],
                "feedback_ids": ["test-feedback-id"]
            }
        ]
    }
    
    # Mock du client Supabase et du service VectorStore
    with patch("app.langgraph.nodes.prioritize.get_supabase_client") as mock_supabase, \
         patch("app.langgraph.nodes.prioritize.VectorStoreService") as mock_vector_store:
        
        # Configurer les mocks
        mock_supabase_instance = MagicMock()
        mock_table = MagicMock()
        mock_supabase_instance.table.return_value = mock_table
        mock_table.insert.return_value = mock_table
        mock_table.update.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = MagicMock()
        
        mock_supabase.return_value = mock_supabase_instance
        
        mock_vector_store_instance = MagicMock()
        mock_vector_store_instance.add_documents = MagicMock()
        mock_vector_store.return_value = mock_vector_store_instance
        
        # Exécuter le nœud
        result_state = await prioritize_stories(input_state)
        
        # Vérifications
        assert "stories" in result_state
        assert len(result_state["stories"]) == 1
        
        # Vérifier que le score RICE a été calculé
        assert "rice_score" in result_state["stories"][0]
        assert result_state["stories"][0]["rice_score"] > 0
        
        # Vérifier que la story a été insérée dans la base de données
        mock_table.insert.assert_called_once()
        
        # Vérifier que le statut du feedback a été mis à jour
        mock_table.update.assert_called()
        
        # Vérifier que la story a été vectorisée
        mock_vector_store_instance.add_documents.assert_called_once()