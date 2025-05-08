from typing import Dict, List, Optional, Union, Any
import json
import uuid

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import SupabaseVectorStore
from langchain.schema.document import Document

from ai_product_pilot.lib.supabase import get_supabase_client
from ai_product_pilot.core.settings import settings


class VectorStoreService:
    """Service pour gérer le stockage vectoriel dans Supabase via pgvector"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
        self.embeddings = OpenAIEmbeddings(openai_api_key=settings.openai_api_key)
        self.vector_store = SupabaseVectorStore(
            client=self.supabase,
            embedding=self.embeddings,
            table_name="documents",
            query_name="match_documents",
        )
    
    async def add_documents(
        self, 
        texts: List[str], 
        metadatas: List[Dict[str, Any]],
        namespace: Optional[str] = None
    ) -> List[str]:
        """
        Ajoute des documents au stockage vectoriel
        
        Args:
            texts: Liste des contenus textuels
            metadatas: Liste des métadonnées correspondantes
            namespace: Espace de noms optionnel pour regrouper les documents
            
        Returns:
            Liste des IDs des documents ajoutés
        """
        documents = []
        ids = []
        
        for i, (text, metadata) in enumerate(zip(texts, metadatas)):
            doc_id = str(uuid.uuid4())
            ids.append(doc_id)
            
            # Ajouter l'espace de noms aux métadonnées si fourni
            if namespace:
                metadata["namespace"] = namespace
            
            documents.append(
                Document(
                    page_content=text,
                    metadata={
                        "id": doc_id,
                        **metadata
                    }
                )
            )
        
        await self.vector_store.aadd_documents(documents)
        return ids
    
    async def search(
        self, 
        query: str, 
        limit: int = 5,
        filter_type: Optional[str] = None
    ) -> List[Dict]:
        """
        Recherche des documents similaires à la requête
        
        Args:
            query: Texte de recherche
            limit: Nombre maximum de résultats
            filter_type: Type de document à filtrer (feedback ou story)
            
        Returns:
            Liste des documents correspondants
        """
        # Construire le filtre
        filter_dict = {}
        if filter_type:
            filter_dict["type"] = filter_type
        
        # Effectuer la recherche
        results = await self.vector_store.asimilarity_search_with_score(
            query=query,
            k=limit,
            filter=filter_dict if filter_dict else None
        )
        
        # Transformer les résultats
        processed_results = []
        for doc, score in results:
            result = {
                "id": doc.metadata.get("id"),
                "content": doc.page_content,
                "similarity": score,
                **{k: v for k, v in doc.metadata.items() if k != "id"}
            }
            processed_results.append(result)
            
        return processed_results
    
    async def delete_by_ids(self, ids: List[str]) -> None:
        """Supprime des documents par leurs IDs"""
        for doc_id in ids:
            self.supabase.table("documents").delete().eq("metadata->>id", doc_id).execute()