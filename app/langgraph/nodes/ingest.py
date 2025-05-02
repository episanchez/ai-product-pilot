from typing import Dict, List, Any
import json
import csv
import io
from langchain.text_splitter import RecursiveCharacterTextSplitter

from app.supabase.client import get_supabase_client
from app.services.vector_store import VectorStoreService


async def ingest_feedback(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Nœud d'ingestion qui charge les données de feedback et les prépare pour l'analyse
    
    Args:
        state: État actuel contenant feedback_id et feedback_data
        
    Returns:
        État mis à jour avec les documents extraits
    """
    feedback_id = state["feedback_id"]
    feedback_data = state["feedback_data"]
    
    supabase = get_supabase_client()
    vector_store = VectorStoreService()
    
    # Traitement différent selon le type de contenu
    content = ""
    
    # Si le feedback a un fichier associé, le récupérer depuis Supabase Storage
    if feedback_data.get("file_path"):
        file_path = feedback_data["file_path"]
        file_extension = file_path.split(".")[-1].lower()
        
        # Télécharger le fichier
        file_data = supabase.storage.from_("feedback_raw").download(file_path)
        
        # Traiter selon le type de fichier
        if file_extension == "json":
            # Charger le JSON
            try:
                json_data = json.loads(file_data.decode("utf-8"))
                
                # Si c'est une liste de commentaires/avis
                if isinstance(json_data, list):
                    content = "\n\n".join([
                        json.dumps(item, ensure_ascii=False) 
                        for item in json_data
                    ])
                else:
                    content = json.dumps(json_data, ensure_ascii=False, indent=2)
            except json.JSONDecodeError:
                content = f"Erreur de parsing JSON: {file_data.decode('utf-8')}"
        
        elif file_extension == "csv":
            # Charger le CSV
            try:
                csv_data = csv.DictReader(io.StringIO(file_data.decode("utf-8")))
                rows = list(csv_data)
                content = "\n\n".join([
                    ", ".join([f"{k}: {v}" for k, v in row.items()])
                    for row in rows
                ])
            except Exception as e:
                content = f"Erreur de parsing CSV: {str(e)}"
        
        else:
            # Fichier texte par défaut
            content = file_data.decode("utf-8")
    
    # Si le feedback a du contenu textuel direct, l'utiliser
    elif feedback_data.get("content"):
        content = feedback_data["content"]
    
    # Si on a une description, l'ajouter au contenu
    if feedback_data.get("description"):
        content = f"{feedback_data['description']}\n\n{content}"
    
    # Mettre à jour le feedback avec le contenu extrait
    supabase.table("feedback").update({
        "content": content,
        "status": "ingested"
    }).eq("id", feedback_id).execute()
    
    # Découper le contenu en segments pour vectorisation
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    text_chunks = text_splitter.split_text(content)
    
    # Créer les métadonnées pour chaque segment
    metadatas = [{
        "feedback_id": feedback_id,
        "source": feedback_data.get("source", ""),
        "title": feedback_data.get("title", ""),
        "type": "feedback"
    } for _ in text_chunks]
    
    # Vectoriser et stocker les segments
    doc_ids = await vector_store.add_documents(
        texts=text_chunks,
        metadatas=metadatas,
        namespace=f"feedback:{feedback_id}"
    )
    
    # Préparation des documents pour l'étape suivante
    docs = [
        {
            "id": doc_id,
            "content": chunk,
            "metadata": metadata
        }
        for doc_id, chunk, metadata in zip(doc_ids, text_chunks, metadatas)
    ]
    
    # Mettre à jour l'état
    return {
        **state,
        "docs": docs
    }