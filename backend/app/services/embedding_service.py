"""
Embedding service for generating text embeddings.
Supports local embeddings (sentence-transformers) and OpenAI.
"""
from typing import List, Optional
import numpy as np

from app.config import settings
from app.core.exceptions import ExternalServiceError
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Global model cache for local embeddings
_local_model = None


def get_local_model():
    """Get or initialize the local embedding model."""
    global _local_model
    if _local_model is None:
        from sentence_transformers import SentenceTransformer
        logger.info("Loading local embedding model", model=settings.local_embedding_model)
        _local_model = SentenceTransformer(settings.local_embedding_model)
        logger.info("Local embedding model loaded")
    return _local_model


class EmbeddingService:
    """Service for generating text embeddings."""
    
    def __init__(self):
        self.use_local = settings.use_local_embeddings
        self.dimensions = (
            settings.local_embedding_dimensions 
            if self.use_local 
            else settings.openai_embedding_dimensions
        )
        
        if not self.use_local:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=settings.openai_api_key)
            self.model = settings.openai_embedding_model
    
    async def get_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            Numpy array of embedding values
            
        Raises:
            ExternalServiceError: If generation fails
        """
        if self.use_local:
            return await self._get_local_embedding(text)
        else:
            return await self._get_openai_embedding(text)
    
    async def _get_local_embedding(self, text: str) -> np.ndarray:
        """Generate embedding using local sentence-transformers model."""
        try:
            model = get_local_model()
            # Run in thread to not block async loop
            import asyncio
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None, 
                lambda: model.encode(text, normalize_embeddings=True)
            )
            return np.array(embedding, dtype=np.float32)
        except Exception as e:
            logger.exception("Local embedding generation failed", error=str(e))
            raise ExternalServiceError(
                f"Failed to generate embedding: {str(e)}",
                service="LocalEmbedding"
            )
    
    async def _get_openai_embedding(self, text: str) -> np.ndarray:
        """Generate embedding using OpenAI API."""
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=text,
                dimensions=self.dimensions
            )
            
            embedding = np.array(response.data[0].embedding, dtype=np.float32)
            embedding = self._normalize(embedding)
            
            return embedding
            
        except Exception as e:
            logger.exception("OpenAI embedding generation failed", error=str(e))
            raise ExternalServiceError(
                f"Failed to generate embedding: {str(e)}",
                service="OpenAI"
            )
    
    async def get_embeddings_batch(
        self,
        texts: List[str],
        batch_size: int = 100
    ) -> List[np.ndarray]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            batch_size: Number of texts per batch (for OpenAI)
            
        Returns:
            List of numpy arrays with embeddings
        """
        if not texts:
            return []
        
        if self.use_local:
            return await self._get_local_embeddings_batch(texts)
        else:
            return await self._get_openai_embeddings_batch(texts, batch_size)
    
    async def _get_local_embeddings_batch(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings using local model."""
        try:
            model = get_local_model()
            import asyncio
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None,
                lambda: model.encode(texts, normalize_embeddings=True)
            )
            return [np.array(e, dtype=np.float32) for e in embeddings]
        except Exception as e:
            logger.exception("Local batch embedding failed", error=str(e))
            raise ExternalServiceError(
                f"Failed to generate embeddings: {str(e)}",
                service="LocalEmbedding"
            )
    
    async def _get_openai_embeddings_batch(
        self, 
        texts: List[str], 
        batch_size: int
    ) -> List[np.ndarray]:
        """Generate embeddings using OpenAI API in batches."""
        all_embeddings: List[np.ndarray] = []
        
        try:
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                
                response = await self.client.embeddings.create(
                    model=self.model,
                    input=batch,
                    dimensions=self.dimensions
                )
                
                sorted_data = sorted(response.data, key=lambda x: x.index)
                
                for item in sorted_data:
                    embedding = np.array(item.embedding, dtype=np.float32)
                    embedding = self._normalize(embedding)
                    all_embeddings.append(embedding)
            
            return all_embeddings
            
        except Exception as e:
            logger.exception("OpenAI batch embedding failed", error=str(e))
            raise ExternalServiceError(
                f"Failed to generate embeddings: {str(e)}",
                service="OpenAI"
            )
    
    def _normalize(self, embedding: np.ndarray) -> np.ndarray:
        """L2 normalize an embedding vector."""
        norm = np.linalg.norm(embedding)
        if norm > 0:
            return embedding / norm
        return embedding
    
    @staticmethod
    def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between two normalized vectors."""
        return float(np.dot(a, b))
