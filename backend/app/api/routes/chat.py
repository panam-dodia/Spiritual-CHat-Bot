from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from app.services.vector_service import vector_service
from app.services.embedding_service import embedding_service
from app.services.content_filter import content_filter
import openai
from app.core.config import settings

router = APIRouter()


def _require_vector_service():
    if vector_service is None:
        raise HTTPException(status_code=503, detail="Vector database service is unavailable")
    return vector_service

class ChatRequest(BaseModel):
    question: str
    max_context_chunks: int = 3
    collection_name: Optional[str] = None

class SearchRequest(BaseModel):
    query: str
    max_results: int = 5
    collection_name: Optional[str] = None
    filter_document: Optional[str] = None

@router.post("/search")
async def search_documents(request: SearchRequest):
    """
    Search through uploaded documents using semantic similarity.
    
    - **query**: Search query/question
    - **max_results**: Maximum number of results to return  
    - **collection_name**: Specific collection to search (optional)
    - **filter_document**: Filter by specific document name (optional)
    """
    try:
        # Prepare metadata filter
        filter_metadata = {}
        if request.filter_document:
            filter_metadata["document_name"] = request.filter_document
        
        # Search vector database
        results = await _require_vector_service().search_similar_chunks(
            query=request.query,
            n_results=request.max_results,
            collection_name=request.collection_name,
            filter_metadata=filter_metadata if filter_metadata else None
        )
        
        return {
            "status": "success",
            "search_query": request.query,
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@router.post("/chat")
async def chat_with_documents(request: ChatRequest):
    """
    Chat with uploaded documents using RAG (Retrieval Augmented Generation).
    
    - **question**: Your question about the documents
    - **max_context_chunks**: Number of relevant chunks to include as context
    - **collection_name**: Specific collection to search (optional)
    """
    try:
        # First, filter the incoming question for inappropriate content
        content_analysis = content_filter.filter_and_respond(request.question)
        
        # If content should be blocked, return the filtered response
        if not content_analysis["allow_continue"]:
            # Log concerning content for review
            content_filter.log_concerning_content(content_analysis)
            
            return {
                "status": "content_filtered",
                "question": request.question,
                "answer": content_analysis["filtered_response"],
                "content_warning": True,
                "crisis_detected": content_analysis["crisis_check"]["crisis_detected"]
            }
        
        # Search for relevant context
        search_results = await _require_vector_service().search_similar_chunks(
            query=request.question,
            n_results=request.max_context_chunks,
            collection_name=request.collection_name
        )
        
        if not search_results["results"]:
            return {
                "status": "no_context",
                "question": request.question,
                "answer": "I couldn't find any relevant information in the uploaded documents to answer your question.",
                "context_used": []
            }
        
        # Prepare context from search results
        context_chunks = []
        for result in search_results["results"]:
            context_chunks.append({
                "text": result["text"],
                "document": result["metadata"].get("document_name", "Unknown"),
                "similarity": result["similarity_score"]
            })
        
        # Create context string for the LLM
        context_text = "\n\n".join([
            f"From {chunk['document']} (Relevance: {chunk['similarity']:.2f}):\n{chunk['text']}"
            for chunk in context_chunks
        ])
        
        # Create the prompt for OpenAI
        system_prompt = """You are a helpful spiritual assistant. Use the provided context from spiritual documents to answer questions. Follow these guidelines:

1. Base your answers primarily on the provided context
2. Be respectful and compassionate in your responses
3. If the context doesn't contain enough information, say so honestly
4. Provide specific references to the source documents when possible
5. For sensitive topics, encourage seeking guidance from spiritual leaders
6. If someone expresses crisis thoughts, provide crisis resources and encourage professional help

Context from spiritual documents:
{context}"""

        user_prompt = f"Question: {request.question}"
        
        # Call OpenAI for the response
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model=settings.CHAT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt.format(context=context_text)},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        answer = response.choices[0].message.content
        
        # Filter the generated response as well
        response_analysis = content_filter.filter_and_respond(answer)
        if not response_analysis["allow_continue"]:
            answer = "I apologize, but I cannot provide a response to this question. Please consider speaking with a qualified spiritual counselor for guidance on this topic."
        
        return {
            "status": "success",
            "question": request.question,
            "answer": answer,
            "context_used": context_chunks,
            "content_filtered": not content_analysis["allow_continue"],
            "total_tokens_used": response.usage.total_tokens if response.usage else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")

@router.get("/collections")
async def list_collections():
    """List all available document collections."""
    try:
        # Simple approach - just return the default collection info
        default_collection = _require_vector_service().get_collection_info()
        
        return {
            "status": "success",
            "collections": [default_collection],
            "note": "Showing default collection. ChromaDB v0.6.0 has API changes."
        }
        
    except Exception as e:
        # If even that fails, return a basic response
        return {
            "status": "partial_success",
            "collections": [{
                "name": "spiritual_documents",
                "total_chunks": "unknown",
                "metadata": {},
                "note": "Collection exists but info unavailable due to ChromaDB API changes"
            }],
            "error": str(e)
        }

@router.get("/collections/{collection_name}")
async def get_collection_info(collection_name: str):
    """Get detailed information about a specific collection."""
    try:
        info = _require_vector_service().get_collection_info(collection_name)
        return {
            "status": "success",
            "collection": info
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting collection info: {str(e)}")

@router.delete("/collections/{collection_name}")
async def reset_collection(collection_name: str):
    """Reset (clear) a specific collection."""
    try:
        result = _require_vector_service().reset_collection(collection_name)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting collection: {str(e)}")

@router.get("/test-vector-db")
async def test_vector_db():
    """Test if vector database is working and contains data."""
    try:
        # Try to get the default collection and check its count
        collection = _require_vector_service().get_or_create_collection()
        count = collection.count()
        
        # Try a simple query to test search functionality
        if count > 0:
            test_results = collection.query(
                query_texts=["test"],
                n_results=1,
                include=["documents", "metadatas"]
            )
            
            sample_doc = None
            if test_results['documents'] and test_results['documents'][0]:
                sample_doc = {
                    "text_preview": test_results['documents'][0][0][:200] + "...",
                    "metadata": test_results['metadatas'][0][0]
                }
        else:
            sample_doc = None
        
        return {
            "status": "success",
            "vector_db_working": True,
            "total_chunks": count,
            "collection_name": _require_vector_service().collection_name,
            "sample_document": sample_doc
        }
        
    except Exception as e:
        return {
            "status": "error",
            "vector_db_working": False,
            "error": str(e)
        }

@router.post("/test-content-filter")
async def test_content_filter(text: str):
    """
    Test the content filtering system.
    
    - **text**: Text to analyze for inappropriate or crisis content
    """
    try:
        analysis = content_filter.filter_and_respond(text)
        
        return {
            "status": "success",
            "analysis": analysis
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Content filter error: {str(e)}")

@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    collection_name: Optional[str] = Query(None, description="Collection name")
):
    """Delete a specific document and all its chunks."""
    try:
        result = _require_vector_service().delete_document(document_id, collection_name)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")