"""
Document management endpoints.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user, verify_tenant_access
from app.config import settings
from app.core.exceptions import (
    ResourceNotFoundError,
    ValidationError,
    StorageLimitExceededError,
)
from app.models.user import User
from app.schemas.document import (
    DocumentResponse,
    DocumentListResponse,
    DocumentStatsResponse,
    DocumentUploadResponse,
)
from app.services.document_service import DocumentService
from app.utils.logger import get_logger
from app.utils.validators import validate_file_extension, validate_file_size

logger = get_logger(__name__)
router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a document"
)
async def upload_document(
    file: UploadFile = File(..., description="PDF file to upload"),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(verify_tenant_access),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a PDF document for processing.
    
    The document will be:
    1. Validated for type and size
    2. Text extracted from PDF
    3. Chunked into smaller pieces
    4. Embedded using OpenAI
    5. Indexed in FAISS for retrieval
    
    Maximum file size: 10MB
    Supported formats: PDF
    """
    # Validate file
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided"
        )
    
    try:
        validate_file_extension(file.filename, [".pdf"])
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Read file content
    content = await file.read()
    
    try:
        validate_file_size(len(content), settings.max_file_size_mb)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    document_service = DocumentService(db)
    
    try:
        document = await document_service.upload_document(
            tenant_id=tenant_id,
            user_id=current_user.id,
            filename=file.filename,
            content=content
        )
        
        logger.info(
            "Document uploaded",
            document_id=document.id,
            filename=file.filename,
            user_id=current_user.id,
            tenant_id=tenant_id
        )
        
        # Return the upload response from service
        return document
    except StorageLimitExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(
            "Document upload failed",
            error=str(e),
            filename=file.filename
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process document"
        )


@router.get(
    "",
    response_model=DocumentListResponse,
    summary="List documents"
)
async def list_documents(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(verify_tenant_access),
    db: AsyncSession = Depends(get_db)
):
    """
    List all documents in the tenant.
    
    Results are paginated and can be filtered by status.
    """
    document_service = DocumentService(db)
    
    # Convert status_filter string to DocumentStatus enum if provided
    status = None
    if status_filter:
        try:
            from app.models.document import DocumentStatus
            status = DocumentStatus(status_filter)
        except ValueError:
            pass
    
    return await document_service.get_documents(
        tenant_id=tenant_id,
        page=page,
        page_size=page_size,
        status=status
    )


@router.get(
    "/stats",
    response_model=DocumentStatsResponse,
    summary="Get document statistics"
)
async def get_document_stats(
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(verify_tenant_access),
    db: AsyncSession = Depends(get_db)
):
    """
    Get document statistics for the tenant.
    
    Returns counts by status, total storage used, etc.
    """
    document_service = DocumentService(db)
    stats = await document_service.get_document_stats(tenant_id)
    
    return DocumentStatsResponse(**stats)


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Get document by ID"
)
async def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(verify_tenant_access),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific document by ID.
    """
    document_service = DocumentService(db)
    document = await document_service.get_document(document_id, tenant_id)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return DocumentResponse.model_validate(document)


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete document"
)
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(verify_tenant_access),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a document and all its associated data.
    
    This will:
    1. Remove the document record
    2. Delete all chunks
    3. Update the FAISS index
    """
    document_service = DocumentService(db)
    
    try:
        await document_service.delete_document(document_id, tenant_id)
        
        logger.info(
            "Document deleted",
            document_id=document_id,
            deleted_by=current_user.id,
            tenant_id=tenant_id
        )
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )


@router.post(
    "/{document_id}/reprocess",
    response_model=DocumentResponse,
    summary="Reprocess document"
)
async def reprocess_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(verify_tenant_access),
    db: AsyncSession = Depends(get_db)
):
    """
    Reprocess a failed document.
    
    This will retry the entire processing pipeline for documents
    that previously failed.
    """
    document_service = DocumentService(db)
    
    document = await document_service.get_document(document_id, tenant_id)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    if document.status != "failed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only failed documents can be reprocessed"
        )
    
    try:
        document = await document_service.reprocess_document(document_id, tenant_id)
        
        logger.info(
            "Document reprocessed",
            document_id=document_id,
            reprocessed_by=current_user.id,
            tenant_id=tenant_id
        )
        
        return DocumentResponse.model_validate(document)
    except Exception as e:
        logger.error(
            "Document reprocessing failed",
            error=str(e),
            document_id=document_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reprocess document"
        )
