from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List, Optional
import structlog

from app.core.database import get_db
from app.core.security import get_current_user_required
from app.models.schemas import (
    KnowledgeEntryCreate,
    KnowledgeEntryUpdate,
    KnowledgeEntryResponse,
    KnowledgeEntryListItem,
    KnowledgeCategoryCreate,
    KnowledgeCategoryResponse,
    UnifiedSearchRequest,
    UnifiedSearchResponse,
)
from app.services.knowledge_service import KnowledgeService
from app.services.unified_search import UnifiedSearchEngine

logger = structlog.get_logger()

router = APIRouter()
knowledge_service = KnowledgeService()
unified_search = UnifiedSearchEngine()


@router.post("/knowledge", response_model=KnowledgeEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_knowledge_entry(
    entry: KnowledgeEntryCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_required),
):
    """
    새로운 지식 항목 생성
    - 태그와 카테고리는 자동으로 추출/분류됩니다 (미제공 시)
    - 벡터 임베딩이 자동으로 생성되어 ChromaDB에 저장됩니다
    """
    try:
        logger.info("Creating knowledge entry", title=entry.title)
        
        result = await knowledge_service.create_knowledge_entry(
            db=db,
            title=entry.title,
            content=entry.content,
            category=entry.category,
            tags=entry.tags,
            source_type="manual",
            author=entry.author,
            status=entry.status,
            user_id=current_user["user_id"],
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error creating knowledge entry: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create knowledge entry: {str(e)}"
        )


@router.get("/knowledge", response_model=List[KnowledgeEntryListItem])
def list_knowledge_entries(
    category: Optional[str] = None,
    tags: Optional[str] = None,  # 쉼표로 구분된 태그
    status_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_required),
):
    """
    지식 항목 목록 조회
    - category, tags, status로 필터링 가능
    - 페이지네이션 지원 (skip, limit)
    """
    try:
        tags_list = tags.split(",") if tags else None
        
        logger.info(
            "Listing knowledge entries",
            category=category,
            tags=tags_list,
            status=status_filter,
            skip=skip,
            limit=limit,
        )
        
        results = knowledge_service.list_knowledge_entries(
            db=db,
            category=category,
            tags=tags_list,
            status=status_filter,
            skip=skip,
            limit=limit,
            user_id=current_user["user_id"],
        )
        
        return results
        
    except Exception as e:
        logger.error(f"Error listing knowledge entries: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list knowledge entries: {str(e)}"
        )


@router.get("/knowledge/{entry_id}", response_model=KnowledgeEntryResponse)
def get_knowledge_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_required),
):
    """특정 지식 항목 조회"""
    try:
        result = knowledge_service.get_knowledge_entry(
            db=db, entry_id=entry_id, user_id=current_user["user_id"]
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledge entry with id {entry_id} not found"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting knowledge entry: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get knowledge entry: {str(e)}"
        )


@router.put("/knowledge/{entry_id}", response_model=KnowledgeEntryResponse)
async def update_knowledge_entry(
    entry_id: int,
    entry: KnowledgeEntryUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_required),
):
    """
    지식 항목 업데이트
    - 변경된 필드만 업데이트됩니다
    - 내용이 변경되면 벡터 임베딩도 자동으로 업데이트됩니다
    """
    try:
        logger.info("Updating knowledge entry", entry_id=entry_id)
        
        result = await knowledge_service.update_knowledge_entry(
            db=db,
            entry_id=entry_id,
            title=entry.title,
            content=entry.content,
            category=entry.category,
            tags=entry.tags,
            status=entry.status,
            user_id=current_user["user_id"],
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating knowledge entry: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update knowledge entry: {str(e)}"
        )


@router.delete("/knowledge/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_knowledge_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_required),
):
    """
    지식 항목 삭제
    - PostgreSQL과 ChromaDB에서 모두 삭제됩니다
    """
    try:
        logger.info("Deleting knowledge entry", entry_id=entry_id)
        
        knowledge_service.delete_knowledge_entry(
            db=db, entry_id=entry_id, user_id=current_user["user_id"]
        )
        return None
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error deleting knowledge entry: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete knowledge entry: {str(e)}"
        )


@router.post("/knowledge/upload", response_model=KnowledgeEntryResponse, status_code=status.HTTP_201_CREATED)
async def upload_knowledge_file(
    file: UploadFile = File(...),
    author: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_required),
):
    """
    파일에서 지식 추출 및 등록
    - 지원 파일: .md, .txt
    - 마크다운 파일의 경우 제목이 자동으로 추출됩니다
    """
    try:
        logger.info("Uploading knowledge file", filename=file.filename)
        
        # 파일 타입 검증
        file_ext = file.filename.split(".")[-1].lower()
        if file_ext not in ["md", "txt"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only .md and .txt files are supported"
            )
        
        # 파일 내용 읽기
        content = await file.read()
        file_content = content.decode("utf-8")
        
        # 지식 추출
        result = await knowledge_service.extract_knowledge_from_file(
            db=db,
            file_content=file_content,
            file_name=file.filename,
            file_type=f".{file_ext}",
            author=author,
            user_id=current_user["user_id"],
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading knowledge file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload knowledge file: {str(e)}"
        )


# 카테고리 관리 API
@router.post("/knowledge/categories", response_model=KnowledgeCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    category: KnowledgeCategoryCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_required),
):
    """새로운 카테고리 생성"""
    try:
        logger.info("Creating knowledge category", name=category.name)
        
        result = knowledge_service.create_category(
            db=db,
            name=category.name,
            description=category.description,
            color=category.color,
            icon=category.icon,
            display_order=category.display_order,
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error creating category: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create category: {str(e)}"
        )


@router.get("/knowledge/categories", response_model=List[KnowledgeCategoryResponse])
def list_categories(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_required),
):
    """카테고리 목록 조회"""
    try:
        results = knowledge_service.list_categories(db=db)
        return results
        
    except Exception as e:
        logger.error(f"Error listing categories: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list categories: {str(e)}"
        )


# 통합 검색 API
@router.post("/search/unified", response_model=UnifiedSearchResponse)
async def unified_search_endpoint(
    request: UnifiedSearchRequest,
    current_user: dict = Depends(get_current_user_required),
):
    """
    통합 검색 API
    - 문서, 지식베이스, 웹에서 병렬 검색
    - 결과를 가중치 기반으로 통합 및 재정렬
    """
    try:
        logger.info(
            "Unified search request",
            query=request.query,
            sources=request.sources,
        )
        
        # 메타데이터 필터 생성
        metadata_filter = {}
        if request.category:
            metadata_filter["category"] = request.category
        if request.tags:
            metadata_filter["tags"] = request.tags
        
        result = await unified_search.search(
            query=request.query,
            sources=request.sources,
            top_k=request.top_k,
            metadata_filter=metadata_filter if metadata_filter else None,
            user_id=current_user["user_id"],
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in unified search: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unified search failed: {str(e)}"
        )
