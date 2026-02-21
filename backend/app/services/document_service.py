"""
Document service for file upload, processing, and management.
Orchestrates PDF processing, chunking, and embedding generation.
"""
import os
import uuid
import aiofiles
from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import (
    NotFoundError,
    ValidationError,
    TenantLimitError,
    DocumentProcessingError,
)
from app.models.document import Document, DocumentChunk, DocumentStatus
from app.repositories.document_repository import DocumentRepository, DocumentChunkRepository
from app.services.tenant_service import TenantService
from app.services.embedding_service import EmbeddingService
from app.services.vector_service import VectorService
from app.utils.pdf_processor import PDFProcessor
from app.utils.text_chunker import TextChunker
from app.utils.validators import compute_file_hash
from app.schemas.document import (
    DocumentResponse,
    DocumentListResponse,
    DocumentUploadResponse,
    RebuildIndexResponse,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DocumentService:
    """Service for document management operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.document_repo = DocumentRepository(session)
        self.chunk_repo = DocumentChunkRepository(session)
        self.tenant_service = TenantService(session)
        self.embedding_service = EmbeddingService()
        self.vector_service = VectorService()
        self.pdf_processor = PDFProcessor()
        self.text_chunker = TextChunker()
        
        # Ensure upload directory exists
        os.makedirs(settings.upload_path, exist_ok=True)
    
    async def upload_document(
        self,
        tenant_id: str,
        user_id: str,
        filename: str,
        content: bytes
    ) -> DocumentUploadResponse:
        """
        Upload and process a new document.
        
        Args:
            tenant_id: Tenant ID
            user_id: Uploading user ID
            filename: Original filename
            content: File content bytes
            
        Returns:
            DocumentUploadResponse
            
        Raises:
            TenantLimitError: If tenant limits exceeded
            ValidationError: If file is invalid
        """
        # Check tenant limits
        can_upload, current, max_docs = await self.tenant_service.check_document_limit(tenant_id)
        if not can_upload:
            raise TenantLimitError(
                "Document limit reached",
                limit_type="documents",
                current_value=current,
                max_value=max_docs
            )
        
        has_space, current_mb, max_mb = await self.tenant_service.check_storage_limit(
            tenant_id, len(content)
        )
        if not has_space:
            raise TenantLimitError(
                "Storage limit reached",
                limit_type="storage_mb",
                current_value=int(current_mb),
                max_value=int(max_mb)
            )
        
        # Compute file hash
        file_hash = compute_file_hash(content)
        
        # Check for duplicate
        existing = await self.document_repo.get_by_hash(file_hash, tenant_id)
        if existing:
            logger.info("Duplicate document detected", document_id=existing.id)
            return DocumentUploadResponse(
                id=existing.id,
                filename=existing.filename,
                original_name=existing.original_name,
                status=existing.status,
                message="Document already exists"
            )
        
        # Generate unique filename
        ext = os.path.splitext(filename)[1]
        stored_filename = f"{uuid.uuid4()}{ext}"
        file_path = os.path.join(settings.upload_path, stored_filename)
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        # Create document record
        document = await self.document_repo.create(
            tenant_id=tenant_id,
            uploaded_by=user_id,
            filename=stored_filename,
            original_name=filename,
            file_size=len(content),
            file_hash=file_hash,
            mime_type="application/pdf",
            status=DocumentStatus.PENDING
        )
        
        logger.info(
            "Document uploaded",
            document_id=document.id,
            filename=filename,
            size=len(content)
        )
        
        # Process document asynchronously
        try:
            await self._process_document(document, file_path)
        except Exception as e:
            logger.exception("Document processing failed", document_id=document.id)
            await self.document_repo.update_status(
                document.id,
                DocumentStatus.FAILED,
                error_message=str(e)
            )
        
        # Refresh document status
        document = await self.document_repo.get_by_id(document.id)
        
        return DocumentUploadResponse(
            id=document.id,
            filename=document.filename,
            original_name=document.original_name,
            status=document.status,
            message="Document uploaded and processed" if document.status == DocumentStatus.COMPLETED else "Document uploaded, processing..."
        )
    
    async def _process_document(self, document: Document, file_path: str) -> None:
        """
        Process a document: extract text, chunk, embed, and index.
        
        Args:
            document: Document record
            file_path: Path to the PDF file
        """
        # Mark as processing
        await self.document_repo.update_status(document.id, DocumentStatus.PROCESSING)
        
        # Extract text
        logger.info("Extracting text", document_id=document.id)
        extraction_result = self.pdf_processor.extract_text(file_path)
        
        if not extraction_result.pages:
            raise DocumentProcessingError(
                "No text could be extracted from PDF",
                document_id=document.id,
                stage="extraction"
            )
        
        # Prepare pages for chunking
        pages = [
            {"text": page.text, "page_number": page.page_number}
            for page in extraction_result.pages
        ]
        
        # Chunk text
        logger.info("Chunking text", document_id=document.id)
        chunks = self.text_chunker.chunk_pages(pages)
        
        if not chunks:
            raise DocumentProcessingError(
                "No chunks could be created from document",
                document_id=document.id,
                stage="chunking"
            )
        
        # Generate embeddings
        logger.info(
            "Generating embeddings",
            document_id=document.id,
            chunks=len(chunks)
        )
        texts = [chunk.content for chunk in chunks]
        embeddings = await self.embedding_service.get_embeddings_batch(texts)
        
        # Store chunks in database
        logger.info("Storing chunks", document_id=document.id)
        chunk_records = []
        for chunk in chunks:
            chunk_record = await self.chunk_repo.create(
                document_id=document.id,
                tenant_id=document.tenant_id,
                chunk_index=chunk.index,
                content=chunk.content,
                token_count=chunk.token_count,
                page_number=chunk.page_number
            )
            chunk_records.append(chunk_record)
        
        # Add to vector index
        logger.info("Adding to vector index", document_id=document.id)
        chunk_ids = [c.id for c in chunk_records]
        embedding_ids = await self.vector_service.add_vectors(
            document.tenant_id,
            chunk_ids,
            embeddings
        )
        
        # Update chunks with embedding IDs
        for chunk_record, embedding_id in zip(chunk_records, embedding_ids):
            chunk_record.embedding_id = embedding_id
        await self.session.flush()
        
        # Mark as completed
        await self.document_repo.update_status(
            document.id,
            DocumentStatus.COMPLETED,
            page_count=extraction_result.total_pages,
            chunk_count=len(chunks)
        )
        
        logger.info(
            "Document processing completed",
            document_id=document.id,
            pages=extraction_result.total_pages,
            chunks=len(chunks)
        )
    
    async def get_document(
        self,
        document_id: str,
        tenant_id: str
    ) -> Document:
        """Get document by ID."""
        document = await self.document_repo.get_by_id(document_id, tenant_id)
        if not document:
            raise NotFoundError(
                "Document not found",
                resource_type="document",
                resource_id=document_id
            )
        return document
    
    async def reprocess_document(
        self,
        document_id: str,
        tenant_id: str
    ) -> Document:
        """
        Reprocess a failed document.
        
        Args:
            document_id: Document ID to reprocess
            tenant_id: Tenant ID
            
        Returns:
            Updated Document
            
        Raises:
            NotFoundError: If document not found
            ValidationError: If document is not in failed status
        """
        document = await self.get_document(document_id, tenant_id)
        
        if document.status != DocumentStatus.FAILED:
            raise ValidationError(
                "Only failed documents can be reprocessed",
                field="status",
                value=document.status.value
            )
        
        # Reset status to pending
        await self.document_repo.update_status(
            document_id,
            DocumentStatus.PENDING,
            error_message=None
        )
        
        # Delete existing chunks if any
        existing_chunks = await self.chunk_repo.get_by_document(document_id, tenant_id)
        if existing_chunks:
            chunk_ids = [c.id for c in existing_chunks]
            await self.vector_service.delete_vectors(tenant_id, chunk_ids)
            for chunk in existing_chunks:
                await self.session.delete(chunk)
            await self.session.flush()
        
        # Get file path
        file_path = os.path.join(settings.upload_path, document.filename)
        
        if not os.path.exists(file_path):
            await self.document_repo.update_status(
                document_id,
                DocumentStatus.FAILED,
                error_message="Original file no longer exists"
            )
            return await self.get_document(document_id, tenant_id)
        
        # Reprocess the document
        try:
            await self._process_document(document, file_path)
        except Exception as e:
            logger.exception("Document reprocessing failed", document_id=document_id)
            await self.document_repo.update_status(
                document_id,
                DocumentStatus.FAILED,
                error_message=str(e)
            )
        
        return await self.get_document(document_id, tenant_id)
    
    async def get_documents(
        self,
        tenant_id: str,
        page: int = 1,
        page_size: int = 20,
        status: Optional[DocumentStatus] = None
    ) -> DocumentListResponse:
        """
        Get paginated list of documents for a tenant.
        """
        skip = (page - 1) * page_size
        
        documents = await self.document_repo.get_by_tenant(
            tenant_id=tenant_id,
            skip=skip,
            limit=page_size,
            status=status
        )
        
        total = await self.document_repo.count_by_tenant(tenant_id, status)
        pages = (total + page_size - 1) // page_size
        
        doc_responses = []
        for doc in documents:
            response = DocumentResponse.model_validate(doc)
            response.file_size_mb = doc.file_size_mb
            doc_responses.append(response)
        
        return DocumentListResponse(
            documents=doc_responses,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages
        )
    
    async def delete_document(
        self,
        document_id: str,
        tenant_id: str
    ) -> bool:
        """
        Delete a document and its associated chunks and vectors.
        """
        document = await self.get_document(document_id, tenant_id)
        
        # Get chunk IDs for vector deletion
        chunks = await self.chunk_repo.get_by_document(document_id, tenant_id)
        chunk_ids = [c.id for c in chunks]
        
        # Delete vectors
        if chunk_ids:
            await self.vector_service.delete_vectors(tenant_id, chunk_ids)
        
        # Delete file
        file_path = os.path.join(settings.upload_path, document.filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Delete document (cascades to chunks)
        await self.document_repo.delete(document)
        
        logger.info(
            "Document deleted",
            document_id=document_id,
            chunks_deleted=len(chunk_ids)
        )
        
        return True
    
    async def rebuild_index(
        self,
        tenant_id: str,
        document_ids: Optional[List[str]] = None
    ) -> RebuildIndexResponse:
        """
        Rebuild FAISS index for a tenant.
        
        Args:
            tenant_id: Tenant ID
            document_ids: Optional specific documents to reindex
            
        Returns:
            RebuildIndexResponse
        """
        if document_ids:
            # Get chunks for specific documents
            all_chunks = []
            for doc_id in document_ids:
                chunks = await self.chunk_repo.get_by_document(doc_id, tenant_id)
                all_chunks.extend(chunks)
        else:
            # Get all chunks for tenant
            all_chunks = await self.chunk_repo.get_all_for_tenant(tenant_id)
        
        if not all_chunks:
            return RebuildIndexResponse(
                success=True,
                documents_processed=0,
                chunks_indexed=0,
                message="No chunks to index"
            )
        
        # Generate embeddings for all chunks
        texts = [c.content for c in all_chunks]
        embeddings = await self.embedding_service.get_embeddings_batch(texts)
        
        # Rebuild index
        chunk_ids = [c.id for c in all_chunks]
        total_vectors = await self.vector_service.rebuild_index(
            tenant_id,
            chunk_ids,
            embeddings
        )
        
        # Update embedding IDs in database
        for i, chunk in enumerate(all_chunks):
            chunk.embedding_id = i
        await self.session.flush()
        
        # Count unique documents
        doc_ids = set(c.document_id for c in all_chunks)
        
        logger.info(
            "Index rebuilt",
            tenant_id=tenant_id,
            documents=len(doc_ids),
            chunks=total_vectors
        )
        
        return RebuildIndexResponse(
            success=True,
            documents_processed=len(doc_ids),
            chunks_indexed=total_vectors,
            message="Index rebuilt successfully"
        )

    async def get_document_stats(self, tenant_id: str) -> dict:
        """
        Get document statistics for a tenant.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            Dict with document statistics
        """
        # Get counts by status
        total = await self.document_repo.count_by_tenant(tenant_id)
        processing = await self.document_repo.count_by_tenant(tenant_id, DocumentStatus.PROCESSING)
        failed = await self.document_repo.count_by_tenant(tenant_id, DocumentStatus.FAILED)
        completed = await self.document_repo.count_by_tenant(tenant_id, DocumentStatus.COMPLETED)
        pending = await self.document_repo.count_by_tenant(tenant_id, DocumentStatus.PENDING)
        
        # Get total storage
        total_bytes = await self.document_repo.get_total_storage(tenant_id)
        total_mb = total_bytes / (1024 * 1024) if total_bytes else 0.0
        
        # Get total chunks
        total_chunks = await self.chunk_repo.count_by_tenant(tenant_id)
        
        return {
            "total_documents": total,
            "total_chunks": total_chunks,
            "total_storage_bytes": total_bytes,
            "total_storage_mb": round(total_mb, 2),
            "documents_by_status": {
                "pending": pending,
                "processing": processing,
                "completed": completed,
                "failed": failed
            },
            "processing_documents": processing,
            "failed_documents": failed
        }
