from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import shutil
import os
from pathlib import Path
import structlog

from app.core.database import get_db
from app.core.security import get_current_user_required
from app.models.document import Document as DBDocument
from app.models.schemas import DocumentUploadResponse, DocumentInfo
from app.services.document_processor import DocumentProcessor
from app.services.chunking import ChunkingService
from app.services.embedding_service import EmbeddingService
from datetime import datetime

logger = structlog.get_logger()
router = APIRouter()

UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


async def process_document_background(
    file_path: str,
    document_id: int,
    user_id: int,
    db: Session,
):
    """Background task to process uploaded document."""
    try:
        doc_processor = DocumentProcessor()
        chunking_service = ChunkingService()
        embedding_service = EmbeddingService()

        doc_processor.validate_file(file_path)
        db_doc = db.query(DBDocument).filter(DBDocument.id == document_id).first()
        original_filename = db_doc.filename if db_doc else Path(file_path).name

        documents = doc_processor.load_document(
            file_path,
            metadata={"user_id": str(user_id), "filename": original_filename},
        )
        
        chunks = chunking_service.chunk_documents(documents, document_id=document_id)
        chunk_ids = [c.metadata["chunk_id"] for c in chunks]
        
        vector_ids = embedding_service.add_documents_to_store(
            documents=chunks,
            collection_name="documents",
            ids=chunk_ids,
        )

        db_doc = db.query(DBDocument).filter(DBDocument.id == document_id).first()
        if db_doc:
            db_doc.status = "completed"
            db_doc.num_chunks = len(chunks)
            db_doc.vector_ids = vector_ids
            db_doc.processed_at = datetime.utcnow()
            db.commit()
        
        logger.info(f"Document processed successfully", document_id=document_id, num_chunks=len(chunks))

    except Exception as e:
        logger.error(f"Error processing document: {str(e)}", document_id=document_id)
        db_doc = db.query(DBDocument).filter(DBDocument.id == document_id).first()
        if db_doc:
            db_doc.status = "failed"
            db_doc.error_message = str(e)
            db.commit()


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_required),
):
    """Upload a document for processing."""
    try:
        file_extension = Path(file.filename).suffix.lower()
        file_path = UPLOAD_DIR / f"{datetime.utcnow().timestamp()}_{file.filename}"
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        file_size = os.path.getsize(file_path)
        
        db_document = DBDocument(
            filename=file.filename,
            file_path=str(file_path),
            file_type=file_extension,
            file_size=file_size,
            status="processing",
            user_id=current_user["user_id"],
        )
        db.add(db_document)
        db.commit()
        db.refresh(db_document)
        
        background_tasks.add_task(
            process_document_background,
            str(file_path),
            db_document.id,
            current_user["user_id"],
            db,
        )
        
        logger.info(f"Document uploaded", filename=file.filename, document_id=db_document.id)
        
        return DocumentUploadResponse(
            id=db_document.id,
            filename=db_document.filename,
            file_type=db_document.file_type,
            file_size=db_document.file_size,
            num_chunks=0,
            status=db_document.status,
            created_at=db_document.created_at,
        )

    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[DocumentInfo])
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_required),
):
    """Get list of all uploaded documents."""
    try:
        documents = (
            db.query(DBDocument)
            .filter(DBDocument.user_id == current_user["user_id"])
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        return [
            DocumentInfo(
                id=doc.id,
                filename=doc.filename,
                file_type=doc.file_type,
                file_size=doc.file_size,
                num_chunks=doc.num_chunks,
                status=doc.status,
                created_at=doc.created_at,
                processed_at=doc.processed_at,
            )
            for doc in documents
        ]

    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}", response_model=DocumentInfo)
async def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_required),
):
    """Get details of a specific document."""
    try:
        document = db.query(DBDocument).filter(
            DBDocument.id == document_id,
            DBDocument.user_id == current_user["user_id"],
        ).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return DocumentInfo(
            id=document.id,
            filename=document.filename,
            file_type=document.file_type,
            file_size=document.file_size,
            num_chunks=document.num_chunks,
            status=document.status,
            created_at=document.created_at,
            processed_at=document.processed_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}/content")
async def get_document_content(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_required),
):
    """SQL/텍스트 파일의 원본 내용을 반환합니다."""
    try:
        document = db.query(DBDocument).filter(
            DBDocument.id == document_id,
            DBDocument.user_id == current_user["user_id"],
        ).first()

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        text_types = {".sql", ".tst", ".txt", ".md", ".csv"}
        if document.file_type not in text_types:
            raise HTTPException(
                status_code=400,
                detail=f"Content preview not supported for {document.file_type} files",
            )

        if not os.path.exists(document.file_path):
            raise HTTPException(status_code=404, detail="File not found on disk")

        content = None
        for enc in ["utf-8", "utf-8-sig", "euc-kr", "cp949", "latin-1"]:
            try:
                with open(document.file_path, "r", encoding=enc) as f:
                    content = f.read()
                break
            except (UnicodeDecodeError, LookupError):
                continue

        if content is None:
            raise HTTPException(status_code=500, detail="Could not decode file with any supported encoding")

        return {
            "id": document.id,
            "filename": document.filename,
            "file_type": document.file_type,
            "content": content,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading document content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_required),
):
    """Delete a document and its chunks from the system (DB + ChromaDB)."""
    try:
        document = db.query(DBDocument).filter(
            DBDocument.id == document_id,
            DBDocument.user_id == current_user["user_id"],
        ).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # ChromaDB에서 벡터 삭제
        if getattr(document, "vector_ids", None) and document.vector_ids:
            embedding_service = EmbeddingService()
            embedding_service.delete_documents(
                document_ids=document.vector_ids,
                collection_name="documents",
            )
        
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
        
        db.delete(document)
        db.commit()
        
        logger.info(f"Document deleted", document_id=document_id)
        
        return {"message": "Document deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
