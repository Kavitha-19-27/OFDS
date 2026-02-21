"""
Document and DocumentChunk repositories.
"""
from typing import Optional, List
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentChunk, DocumentStatus
from app.repositories.base import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    """Repository for Document model operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Document, session)
    
    async def get_by_tenant(
        self,
        tenant_id: str,
        skip: int = 0,
        limit: int = 100,
        status: Optional[DocumentStatus] = None
    ) -> List[Document]:
        """
        Get documents for a tenant with optional status filter.
        
        Args:
            tenant_id: Tenant ID
            skip: Records to skip
            limit: Max records
            status: Optional status filter
            
        Returns:
            List of documents
        """
        query = select(Document).where(Document.tenant_id == tenant_id)
        
        if status:
            query = query.where(Document.status == status)
        
        query = query.order_by(Document.created_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_by_hash(
        self,
        file_hash: str,
        tenant_id: str
    ) -> Optional[Document]:
        """
        Find document by file hash (for deduplication).
        
        Args:
            file_hash: SHA-256 hash
            tenant_id: Tenant ID
            
        Returns:
            Document or None
        """
        query = select(Document).where(
            and_(
                Document.file_hash == file_hash,
                Document.tenant_id == tenant_id
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_pending_documents(
        self,
        tenant_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Document]:
        """
        Get documents pending processing.
        
        Args:
            tenant_id: Optional tenant filter
            limit: Max documents to return
            
        Returns:
            List of pending documents
        """
        query = select(Document).where(Document.status == DocumentStatus.PENDING)
        
        if tenant_id:
            query = query.where(Document.tenant_id == tenant_id)
        
        query = query.order_by(Document.created_at).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_total_storage(self, tenant_id: str) -> int:
        """
        Get total storage used by a tenant in bytes.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            Total bytes used
        """
        query = select(func.sum(Document.file_size)).where(
            Document.tenant_id == tenant_id
        )
        result = await self.session.execute(query)
        return result.scalar_one() or 0
    
    async def count_by_tenant(
        self,
        tenant_id: str,
        status: Optional[DocumentStatus] = None
    ) -> int:
        """
        Count documents for a tenant.
        
        Args:
            tenant_id: Tenant ID
            status: Optional status filter
            
        Returns:
            Document count
        """
        query = select(func.count(Document.id)).where(
            Document.tenant_id == tenant_id
        )
        
        if status:
            query = query.where(Document.status == status)
        
        result = await self.session.execute(query)
        return result.scalar_one()
    
    async def update_status(
        self,
        document_id: str,
        status: DocumentStatus,
        error_message: Optional[str] = None,
        page_count: Optional[int] = None,
        chunk_count: Optional[int] = None
    ) -> Optional[Document]:
        """
        Update document processing status.
        
        Args:
            document_id: Document ID
            status: New status
            error_message: Optional error message
            page_count: Optional page count
            chunk_count: Optional chunk count
            
        Returns:
            Updated document or None
        """
        document = await self.get_by_id(document_id)
        if document:
            document.status = status
            if error_message is not None:
                document.error_message = error_message
            if page_count is not None:
                document.page_count = page_count
            if chunk_count is not None:
                document.chunk_count = chunk_count
            await self.session.flush()
            await self.session.refresh(document)
        return document


class DocumentChunkRepository(BaseRepository[DocumentChunk]):
    """Repository for DocumentChunk model operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(DocumentChunk, session)
    
    async def get_by_document(
        self,
        document_id: str,
        tenant_id: str
    ) -> List[DocumentChunk]:
        """
        Get all chunks for a document.
        
        Args:
            document_id: Document ID
            tenant_id: Tenant ID
            
        Returns:
            List of chunks ordered by index
        """
        query = (
            select(DocumentChunk)
            .where(
                and_(
                    DocumentChunk.document_id == document_id,
                    DocumentChunk.tenant_id == tenant_id
                )
            )
            .order_by(DocumentChunk.chunk_index)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_by_ids(
        self,
        chunk_ids: List[str],
        tenant_id: str
    ) -> List[DocumentChunk]:
        """
        Get chunks by IDs.
        
        Args:
            chunk_ids: List of chunk IDs
            tenant_id: Tenant ID
            
        Returns:
            List of chunks
        """
        if not chunk_ids:
            return []
        
        query = select(DocumentChunk).where(
            and_(
                DocumentChunk.id.in_(chunk_ids),
                DocumentChunk.tenant_id == tenant_id
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_by_embedding_ids(
        self,
        embedding_ids: List[int],
        tenant_id: str
    ) -> List[DocumentChunk]:
        """
        Get chunks by FAISS embedding IDs.
        
        Args:
            embedding_ids: FAISS index positions
            tenant_id: Tenant ID
            
        Returns:
            List of chunks
        """
        if not embedding_ids:
            return []
        
        query = select(DocumentChunk).where(
            and_(
                DocumentChunk.embedding_id.in_(embedding_ids),
                DocumentChunk.tenant_id == tenant_id
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def delete_by_document(
        self,
        document_id: str,
        tenant_id: str
    ) -> int:
        """
        Delete all chunks for a document.
        
        Args:
            document_id: Document ID
            tenant_id: Tenant ID
            
        Returns:
            Number of deleted chunks
        """
        chunks = await self.get_by_document(document_id, tenant_id)
        count = len(chunks)
        for chunk in chunks:
            await self.session.delete(chunk)
        await self.session.flush()
        return count
    
    async def get_all_for_tenant(
        self,
        tenant_id: str
    ) -> List[DocumentChunk]:
        """
        Get all chunks for a tenant (for index rebuilding).
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            All chunks for the tenant
        """
        query = (
            select(DocumentChunk)
            .where(DocumentChunk.tenant_id == tenant_id)
            .order_by(DocumentChunk.document_id, DocumentChunk.chunk_index)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def count_by_tenant(self, tenant_id: str) -> int:
        """
        Count total chunks for a tenant.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            Chunk count
        """
        query = select(func.count(DocumentChunk.id)).where(
            DocumentChunk.tenant_id == tenant_id
        )
        result = await self.session.execute(query)
        return result.scalar_one()
