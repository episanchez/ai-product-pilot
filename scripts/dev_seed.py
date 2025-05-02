#!/usr/bin/env python
"""
Script pour insérer des données de test dans la base Supabase
"""
import os
import uuid
import json
import asyncio
from typing import List, Dict, Any
from dotenv import load_dotenv

from supabase import create_client, Client

# Charger les variables d'environnement
load_dotenv()

# Configuration Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# Données de test
FEEDBACK_SAMPLES = [
    {
        "title": "Retours après la dernière mise à jour",
        "description": "Compilation des retours utilisateurs sur les réseaux sociaux après la mise à jour v2.5",
        "source": "social_media",
        "content": """
Je trouve que la nouvelle interface est beaucoup plus intuitive, bravo ! Cependant, la fonction de recherche avancée semble plus lente qu'avant.

Le nouveau dashboard est superbe, mais pourquoi avoir supprimé l'accès rapide aux statistiques ? C'était vraiment pratique.

Après la mise à jour, l'application plante systématiquement quand j'essaie d'exporter mes données en PDF. Sur Android 12, Samsung Galaxy S21.

J'adore la nouvelle fonctionnalité de tags automatiques, ça me fait gagner tellement de temps ! Par contre, serait-il possible d'ajouter la possibilité de créer nos propres tags personnalisés ?

L'application est devenue beaucoup plus rapide sur mon iPhone 13, merci pour l'optimisation !
        """
    },
    {
        "title": "Résultats du sondage satisfaction Q2 2023",
        "description": "Synthèse des réponses au questionnaire de satisfaction envoyé aux utilisateurs premium",
        "source": "survey",
        "content": """
Question 1: Sur une échelle de 1 à 10, quelle est votre satisfaction globale avec notre produit ?
Moyenne: 7.8/10
Commentaires: 
- "Très satisfait mais quelques bugs persistent"
- "J'aimerais plus de fonctionnalités d'analyse"
- "Le service client est excellent"

Question 2: Quelle fonctionnalité utilisez-vous le plus ?
Top réponses:
1. Rapports automatiques (45%)
2. Tableaux de bord personnalisables (32%)
3. Intégration avec d'autres outils (18%)

Question 3: Qu'est-ce qui pourrait être amélioré ?
Top suggestions:
1. Performance sur mobile (37 mentions)
2. Plus d'options d'export (29 mentions)
3. Interface plus simple pour les nouveaux utilisateurs (24 mentions)
4. Meilleure documentation (18 mentions)

Question 4: Recommanderiez-vous notre produit ?
NPS: 42 (Promoteurs: 52%, Passifs: 38%, Détracteurs: 10%)
        """
    },
    {
        "title": "Commentaires du support client - Mai 2023",
        "description": "Données extraites de notre système de tickets support pour le mois de mai",
        "source": "customer_support",
        "content": """
Ticket #4528:
Le client signale que le processus d'authentification à deux facteurs échoue fréquemment sur Firefox. Impossible de se connecter depuis 3 jours. Niveau de frustration: Élevé. 
Résolution: Problème confirmé, bug référencé DEV-892.

Ticket #4532:
Client mécontent de la nouvelle tarification. "Je n'utilise que 3 fonctionnalités sur 20, pourquoi devrais-je payer pour tout ?" Suggère un modèle à la carte.
Résolution: Expliqué la stratégie de prix, offert 20% de réduction pour fidélité.

Ticket #4545:
Suggestion d'amélioration: client demande une fonctionnalité de programmation des rapports (envoi automatique par email chaque lundi).
Résolution: Ajouté à la liste des demandes de fonctionnalités, 12 demandes similaires ce mois-ci.

Ticket #4563:
Bug critique: perte de données lors de l'importation de fichiers Excel volumineux (>10MB).
Résolution: Contournement proposé, escaladé en priorité haute pour l'équipe dev.

Ticket #4570:
Compliment: client très satisfait de la réactivité des équipes après signalement d'un problème la semaine dernière. "Votre support est exceptionnel, merci infiniment !"
        """
    }
]


async def seed_database():
    """Peuple la base de données avec des échantillons de test"""
    
    # Créer le client Supabase
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise ValueError("Les variables SUPABASE_URL et SUPABASE_SERVICE_KEY doivent être définies")
    
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    
    # Vérifier si les tables existent
    try:
        supabase.table("feedback").select("id").limit(1).execute()
        print("✅ Connexion à Supabase établie")
    except Exception as e:
        print(f"❌ Erreur de connexion ou table manquante: {str(e)}")
        print("Assurez-vous d'avoir exécuté les migrations SQL")
        return
    
    # Insérer les feedbacks de test
    for sample in FEEDBACK_SAMPLES:
        feedback_id = str(uuid.uuid4())
        
        feedback_data = {
            "id": feedback_id,
            "title": sample["title"],
            "description": sample["description"],
            "source": sample["source"],
            "content": sample["content"],
            "status": "pending"
        }
        
        try:
            result = supabase.table("feedback").insert(feedback_data).execute()
            print(f"✅ Feedback '{sample['title']}' inséré avec ID: {feedback_id}")
        except Exception as e:
            print(f"❌ Erreur lors de l'insertion du feedback: {str(e)}")
    
    print("\n🚀 Données de test insérées avec succès!")
    print("Vous pouvez maintenant utiliser l'API pour traiter ces feedbacks.")
    print("\nExemple de commande curl pour traiter le premier feedback:")
    
    # Récupérer le premier ID de feedback pour l'exemple
    try:
        result = supabase.table("feedback").select("id").limit(1).execute()
        if result.data:
            first_id = result.data[0]["id"]
            print(f"curl -X POST http://localhost:8000/api/feedback/process/{first_id} -H \"Authorization: Bearer YOUR_JWT_TOKEN\"")
    except Exception:
        print("curl -X POST http://localhost:8000/api/feedback/process/FEEDBACK_ID -H \"Authorization: Bearer YOUR_JWT_TOKEN\"")


if __name__ == "__main__":
    asyncio.run(seed_database())