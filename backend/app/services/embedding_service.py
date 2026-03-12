from typing import List
import openai
from app.core.config import settings

class EmbeddingService:
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.EMBEDDING_MODEL
    
    async def create_embedding(self, text: str) -> List[float]:
        """Create embedding for a single text."""
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            raise Exception(f"Failed to create embedding: {str(e)}")
    
    async def test_connection(self) -> dict:
        """Test OpenAI API connection."""
        try:
            test_text = "This is a test message for spiritual guidance."
            embedding = await self.create_embedding(test_text)
            return {
                "status": "success",
                "message": "OpenAI connection successful",
                "embedding_dimension": len(embedding),
                "model": self.model
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"OpenAI connection failed: {str(e)}"
            }

# Create singleton instance
embedding_service = EmbeddingService()