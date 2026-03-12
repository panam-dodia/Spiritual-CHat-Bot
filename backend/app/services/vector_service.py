# Update your backend/app/services/vector_service.py to avoid the ONNX issue
# Replace the current import section with this:

import os
import uuid
from typing import List, Dict, Any, Optional

# Set environment variable to avoid ONNX dependency
os.environ["ALLOW_RESET"] = "TRUE"

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError as e:
    print(f"Warning: ChromaDB not available: {e}")
    CHROMADB_AVAILABLE = False

class VectorService:
    def __init__(self):
        if not CHROMADB_AVAILABLE:
            raise ImportError("ChromaDB is not available")
        
        # Initialize ChromaDB with explicit settings to avoid ONNX
        self.client = chromadb.PersistentClient(
            path="./data/chroma",
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        self.collection_name = "spiritual_documents"
        
    def get_or_create_collection(self, collection_name: str = None):
        """Get or create a collection without default embedding function"""
        name = collection_name or self.collection_name
        try:
            # Get existing collection
            collection = self.client.get_collection(name=name)
        except Exception:
            # Create new collection without embedding function (we'll provide embeddings)
            collection = self.client.create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"}
            )
        return collection
    
    def add_documents(
        self, 
        texts: List[str], 
        embeddings: List[List[float]], 
        metadatas: List[Dict[str, Any]], 
        ids: Optional[List[str]] = None,
        collection_name: str = None
    ):
        """Add documents with pre-computed embeddings"""
        collection = self.get_or_create_collection(collection_name)
        
        # Generate IDs if not provided
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in texts]
        
        collection.add(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        
        return ids
    
    def search_documents(
        self, 
        query_embedding: List[float], 
        n_results: int = 5,
        collection_name: str = None,
        where: Optional[Dict] = None
    ):
        """Search for similar documents using query embedding"""
        collection = self.get_or_create_collection(collection_name)
        
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where
        )
        
        return results
    
    def delete_documents(self, ids: List[str], collection_name: str = None):
        """Delete documents by IDs"""
        collection = self.get_or_create_collection(collection_name)
        collection.delete(ids=ids)
    
    def get_collection_info(self, collection_name: str = None):
        """Get information about a collection"""
        collection = self.get_or_create_collection(collection_name)
        return {
            "name": collection.name,
            "count": collection.count(),
            "metadata": collection.metadata
        }
    
    def reset_collection(self, collection_name: str = None):
        """Reset/clear a collection"""
        name = collection_name or self.collection_name
        try:
            self.client.delete_collection(name=name)
        except Exception:
            pass  # Collection might not exist
        
        # Recreate empty collection
        return self.get_or_create_collection(name)

    async def search_similar_chunks(
        self,
        query: str,
        n_results: int = 5,
        collection_name: str = None,
        filter_metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Search for similar chunks using a text query (handles embedding internally)."""
        from app.services.embedding_service import embedding_service

        query_embedding = await embedding_service.create_embedding(query)
        raw_results = self.search_documents(
            query_embedding=query_embedding,
            n_results=n_results,
            collection_name=collection_name,
            where=filter_metadata
        )

        formatted_results = []
        if raw_results and raw_results.get("documents") and raw_results["documents"][0]:
            documents = raw_results["documents"][0]
            metadatas = raw_results.get("metadatas", [[]])[0]
            distances = raw_results.get("distances", [[]])[0]
            ids = raw_results.get("ids", [[]])[0]

            for i, doc in enumerate(documents):
                similarity_score = 1 - distances[i] if distances else 0.0
                formatted_results.append({
                    "text": doc,
                    "metadata": metadatas[i] if i < len(metadatas) else {},
                    "similarity_score": round(similarity_score, 4),
                    "id": ids[i] if i < len(ids) else None
                })

        return {"results": formatted_results}

    def delete_document(self, document_id: str, collection_name: str = None) -> Dict[str, Any]:
        """Delete all chunks belonging to a specific document."""
        collection = self.get_or_create_collection(collection_name)
        collection.delete(where={"document_id": document_id})
        return {"status": "success", "deleted_document_id": document_id}


# Create singleton instance
vector_service = VectorService() if CHROMADB_AVAILABLE else None