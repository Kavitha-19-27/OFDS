"""
Vector service for FAISS index management.
Provides per-tenant vector storage with caching.
"""
import os
import pickle
from typing import List, Optional, Tuple, Dict, Any
from collections import OrderedDict
import numpy as np
import faiss

from app.config import settings
from app.core.exceptions import DocumentProcessingError
from app.utils.logger import get_logger

logger = get_logger(__name__)


class LRUCache:
    """Simple LRU cache for FAISS indexes."""
    
    def __init__(self, max_size: int = 10):
        self.max_size = max_size
        self.cache: OrderedDict = OrderedDict()
    
    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        return None
    
    def put(self, key: str, value: Any) -> None:
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            if len(self.cache) >= self.max_size:
                oldest = next(iter(self.cache))
                del self.cache[oldest]
                logger.debug("Evicted index from cache", tenant_id=oldest)
        self.cache[key] = value
    
    def remove(self, key: str) -> None:
        if key in self.cache:
            del self.cache[key]


class VectorService:
    """
    Service for FAISS vector index operations.
    Each tenant has a separate index for strict isolation.
    """
    
    def __init__(self):
        self.index_path = settings.faiss_index_path
        # Use local embedding dimensions if local embeddings are enabled
        self.dimensions = (
            settings.local_embedding_dimensions 
            if settings.use_local_embeddings 
            else settings.openai_embedding_dimensions
        )
        self._cache = LRUCache(max_size=settings.faiss_cache_size)
        
        # Ensure index directory exists
        os.makedirs(self.index_path, exist_ok=True)
    
    def _get_tenant_dir(self, tenant_id: str) -> str:
        """Get directory path for tenant's index."""
        return os.path.join(self.index_path, f"tenant_{tenant_id}")
    
    def _get_index_path(self, tenant_id: str) -> str:
        """Get FAISS index file path for tenant."""
        return os.path.join(self._get_tenant_dir(tenant_id), "index.faiss")
    
    def _get_mapping_path(self, tenant_id: str) -> str:
        """Get ID mapping file path for tenant."""
        return os.path.join(self._get_tenant_dir(tenant_id), "mapping.pkl")
    
    def _create_index(self) -> faiss.IndexFlatIP:
        """
        Create a new FAISS index using Inner Product (cosine similarity for normalized vectors).
        """
        return faiss.IndexFlatIP(self.dimensions)
    
    def _load_index(self, tenant_id: str) -> Tuple[faiss.IndexFlatIP, Dict[int, str]]:
        """
        Load FAISS index and ID mapping for a tenant from disk.
        
        Returns:
            Tuple of (FAISS index, mapping dict)
        """
        # Check cache first
        cached = self._cache.get(tenant_id)
        if cached:
            logger.debug("Index loaded from cache", tenant_id=tenant_id)
            return cached
        
        index_path = self._get_index_path(tenant_id)
        mapping_path = self._get_mapping_path(tenant_id)
        
        if os.path.exists(index_path) and os.path.exists(mapping_path):
            try:
                index = faiss.read_index(index_path)
                with open(mapping_path, 'rb') as f:
                    mapping = pickle.load(f)
                
                # Cache it
                self._cache.put(tenant_id, (index, mapping))
                
                logger.info(
                    "Index loaded from disk",
                    tenant_id=tenant_id,
                    vectors=index.ntotal
                )
                
                return index, mapping
            except Exception as e:
                logger.error("Failed to load index", tenant_id=tenant_id, error=str(e))
        
        # Return new empty index
        index = self._create_index()
        mapping: Dict[int, str] = {}
        return index, mapping
    
    def _save_index(
        self,
        tenant_id: str,
        index: faiss.IndexFlatIP,
        mapping: Dict[int, str]
    ) -> None:
        """
        Save FAISS index and mapping to disk.
        """
        tenant_dir = self._get_tenant_dir(tenant_id)
        os.makedirs(tenant_dir, exist_ok=True)
        
        index_path = self._get_index_path(tenant_id)
        mapping_path = self._get_mapping_path(tenant_id)
        
        try:
            faiss.write_index(index, index_path)
            with open(mapping_path, 'wb') as f:
                pickle.dump(mapping, f)
            
            # Update cache
            self._cache.put(tenant_id, (index, mapping))
            
            logger.info(
                "Index saved to disk",
                tenant_id=tenant_id,
                vectors=index.ntotal
            )
        except Exception as e:
            logger.exception("Failed to save index", tenant_id=tenant_id, error=str(e))
            raise DocumentProcessingError(
                f"Failed to save vector index: {str(e)}",
                stage="index_save"
            )
    
    async def add_vectors(
        self,
        tenant_id: str,
        chunk_ids: List[str],
        embeddings: List[np.ndarray]
    ) -> List[int]:
        """
        Add vectors to tenant's index.
        
        Args:
            tenant_id: Tenant ID
            chunk_ids: List of document chunk IDs
            embeddings: List of embedding vectors
            
        Returns:
            List of FAISS index positions (embedding_ids)
        """
        if not chunk_ids or not embeddings:
            return []
        
        if len(chunk_ids) != len(embeddings):
            raise ValueError("chunk_ids and embeddings must have same length")
        
        # Load existing index
        index, mapping = self._load_index(tenant_id)
        
        # Get starting position
        start_id = index.ntotal
        
        # Stack embeddings into matrix
        vectors = np.vstack(embeddings).astype(np.float32)
        
        # Add to index
        index.add(vectors)
        
        # Update mapping
        embedding_ids = []
        for i, chunk_id in enumerate(chunk_ids):
            embedding_id = start_id + i
            mapping[embedding_id] = chunk_id
            embedding_ids.append(embedding_id)
        
        # Save index
        self._save_index(tenant_id, index, mapping)
        
        logger.info(
            "Vectors added to index",
            tenant_id=tenant_id,
            new_vectors=len(chunk_ids),
            total_vectors=index.ntotal
        )
        
        return embedding_ids
    
    async def search(
        self,
        tenant_id: str,
        query_embedding: np.ndarray,
        top_k: int = 4
    ) -> List[Tuple[str, float]]:
        """
        Search for similar vectors in tenant's index.
        
        Args:
            tenant_id: Tenant ID
            query_embedding: Query vector
            top_k: Number of results to return
            
        Returns:
            List of (chunk_id, similarity_score) tuples
        """
        index, mapping = self._load_index(tenant_id)
        
        if index.ntotal == 0:
            logger.warning("Empty index for tenant", tenant_id=tenant_id)
            return []
        
        # Ensure query is 2D
        query = query_embedding.reshape(1, -1).astype(np.float32)
        
        # Adjust k if index has fewer vectors
        k = min(top_k, index.ntotal)
        
        # Search
        distances, indices = index.search(query, k)
        
        # Map results back to chunk IDs
        results = []
        for i, idx in enumerate(indices[0]):
            if idx >= 0 and idx in mapping:  # -1 means no result
                chunk_id = mapping[idx]
                score = float(distances[0][i])
                results.append((chunk_id, score))
        
        logger.debug(
            "Vector search completed",
            tenant_id=tenant_id,
            results=len(results),
            top_score=results[0][1] if results else 0
        )
        
        return results
    
    async def delete_vectors(
        self,
        tenant_id: str,
        chunk_ids: List[str]
    ) -> int:
        """
        Delete vectors from tenant's index.
        
        Note: FAISS doesn't support efficient deletion, so we rebuild the index
        excluding the deleted vectors. For production, consider using FAISS IDMap
        or a different vector store.
        
        Args:
            tenant_id: Tenant ID
            chunk_ids: Chunk IDs to delete
            
        Returns:
            Number of vectors deleted
        """
        if not chunk_ids:
            return 0
        
        index, mapping = self._load_index(tenant_id)
        
        if index.ntotal == 0:
            return 0
        
        # Find embedding IDs to delete
        chunk_id_set = set(chunk_ids)
        ids_to_keep = []
        new_mapping: Dict[int, str] = {}
        
        for emb_id, chunk_id in mapping.items():
            if chunk_id not in chunk_id_set:
                ids_to_keep.append(emb_id)
        
        if len(ids_to_keep) == len(mapping):
            # Nothing to delete
            return 0
        
        deleted_count = len(mapping) - len(ids_to_keep)
        
        # Rebuild index with remaining vectors
        if ids_to_keep:
            # Extract vectors to keep
            vectors = []
            for old_id in sorted(ids_to_keep):
                vec = index.reconstruct(old_id)
                vectors.append(vec)
            
            # Create new index
            new_index = self._create_index()
            new_index.add(np.vstack(vectors).astype(np.float32))
            
            # Create new mapping
            for new_id, old_id in enumerate(sorted(ids_to_keep)):
                new_mapping[new_id] = mapping[old_id]
            
            self._save_index(tenant_id, new_index, new_mapping)
        else:
            # All vectors deleted, create empty index
            self._save_index(tenant_id, self._create_index(), {})
        
        logger.info(
            "Vectors deleted from index",
            tenant_id=tenant_id,
            deleted=deleted_count
        )
        
        return deleted_count
    
    async def rebuild_index(
        self,
        tenant_id: str,
        chunk_ids: List[str],
        embeddings: List[np.ndarray]
    ) -> int:
        """
        Completely rebuild tenant's index.
        
        Args:
            tenant_id: Tenant ID
            chunk_ids: All chunk IDs
            embeddings: All embedding vectors
            
        Returns:
            Number of vectors in new index
        """
        # Clear cache
        self._cache.remove(tenant_id)
        
        # Create fresh index
        index = self._create_index()
        mapping: Dict[int, str] = {}
        
        if chunk_ids and embeddings:
            vectors = np.vstack(embeddings).astype(np.float32)
            index.add(vectors)
            
            for i, chunk_id in enumerate(chunk_ids):
                mapping[i] = chunk_id
        
        self._save_index(tenant_id, index, mapping)
        
        logger.info(
            "Index rebuilt",
            tenant_id=tenant_id,
            vectors=index.ntotal
        )
        
        return index.ntotal
    
    async def get_index_stats(self, tenant_id: str) -> Dict[str, Any]:
        """
        Get statistics for tenant's index.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            Dict with index statistics
        """
        index, mapping = self._load_index(tenant_id)
        
        return {
            "tenant_id": tenant_id,
            "total_vectors": index.ntotal,
            "dimensions": self.dimensions,
            "index_type": "IndexFlatIP",
        }
