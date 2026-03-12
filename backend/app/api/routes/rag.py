from fastapi import APIRouter, HTTPException
from app.services.embedding_service import embedding_service

router = APIRouter()

@router.get("/test-openai")
async def test_openai_connection():
    """Test OpenAI API connection."""
    result = await embedding_service.test_connection()
    
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    
    return result

@router.post("/test-embedding")
async def test_embedding(text: str):
    """Test creating an embedding for text."""
    try:
        embedding = await embedding_service.create_embedding(text)
        return {
            "text": text,
            "embedding_dimension": len(embedding),
            "embedding_preview": embedding[:5]  # First 5 values
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))