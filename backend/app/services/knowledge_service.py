from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from langchain.schema import Document
import structlog
from datetime import datetime
import json

from app.models.knowledge import KnowledgeEntry, KnowledgeCategory
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService
from app.services.chunking import ChunkingService

logger = structlog.get_logger()


class KnowledgeService:
    """
    지식 베이스 관리 서비스
    - 지식 항목 생성/수정/삭제
    - 태그 자동 추출
    - 카테고리 자동 분류
    - 벡터 임베딩 생성 및 ChromaDB 저장
    """
    
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.llm_service = LLMService()
        self.chunking_service = ChunkingService()
    
    async def _extract_tags(self, content: str, max_tags: int = 5) -> List[str]:
        """
        LLM을 사용하여 콘텐츠에서 태그 자동 추출
        
        Args:
            content: 지식 항목 내용
            max_tags: 최대 태그 개수
            
        Returns:
            추출된 태그 리스트
        """
        try:
            system_prompt = """당신은 기술 문서에서 핵심 키워드를 추출하는 전문가입니다.
주어진 텍스트에서 가장 중요한 기술 키워드를 추출하세요.

규칙:
- 3-5개의 키워드 추출
- 프로그래밍 언어, 프레임워크, 도구, 개념 등 기술적 용어 우선
- 영어와 한글 모두 가능
- 쉼표로 구분하여 응답
- 추가 설명 없이 키워드만 응답

예시: docker, python, 메모리 누수, FastAPI"""

            response = await self.llm_service.generate_response(
                system_prompt=system_prompt,
                user_message=f"다음 텍스트에서 핵심 키워드를 추출하세요:\n\n{content[:1000]}",
            )
            
            tags = [tag.strip() for tag in response.split(",")]
            tags = [tag for tag in tags if tag][:max_tags]
            
            logger.info(f"Extracted {len(tags)} tags", tags=tags)
            return tags
            
        except Exception as e:
            logger.error(f"Error extracting tags: {str(e)}")
            return []
    
    async def _classify_category(self, title: str, content: str) -> str:
        """
        LLM을 사용하여 지식 항목의 카테고리 자동 분류
        
        Args:
            title: 지식 항목 제목
            content: 지식 항목 내용
            
        Returns:
            분류된 카테고리 (error_fix, tech_share, how_to, best_practice, other)
        """
        try:
            system_prompt = """당신은 기술 문서를 분류하는 전문가입니다.
주어진 문서를 다음 카테고리 중 하나로 분류하세요:

1. error_fix: 에러 해결 방법, 버그 픽스, 트러블슈팅
2. tech_share: 기술 공유, 새로운 기술 소개, 학습 자료
3. how_to: 사용법, 튜토리얼, 가이드
4. best_practice: 모범 사례, 코딩 규칙, 아키텍처 패턴
5. other: 기타

응답은 카테고리 이름만 정확히 반환하세요 (error_fix, tech_share, how_to, best_practice, other 중 하나)."""

            response = await self.llm_service.generate_response(
                system_prompt=system_prompt,
                user_message=f"제목: {title}\n\n내용:\n{content[:500]}",
            )
            
            category = response.strip().lower()
            valid_categories = ["error_fix", "tech_share", "how_to", "best_practice", "other"]
            
            if category not in valid_categories:
                logger.warning(f"Invalid category returned: {category}, defaulting to 'other'")
                category = "other"
            
            logger.info(f"Classified as category: {category}")
            return category
            
        except Exception as e:
            logger.error(f"Error classifying category: {str(e)}")
            return "other"
    
    def _split_knowledge(self, text: str) -> List[str]:
        """
        지식 항목을 적절한 크기의 청크로 분할
        
        Args:
            text: 분할할 텍스트
            
        Returns:
            청크 리스트
        """
        try:
            docs = self.chunking_service.chunk_text(text, metadata={})
            chunks = [doc.page_content for doc in docs]
            
            logger.info(f"Split knowledge into {len(chunks)} chunks")
            return chunks
            
        except Exception as e:
            logger.error(f"Error splitting knowledge: {str(e)}")
            return [text]
    
    async def create_knowledge_entry(
        self,
        db: Session,
        title: str,
        content: str,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        source_type: str = "manual",
        author: Optional[str] = None,
        status: str = "published",
        user_id: Optional[int] = None,
    ) -> KnowledgeEntry:
        """
        새로운 지식 항목 생성 및 벡터화
        
        Args:
            db: 데이터베이스 세션
            title: 지식 항목 제목
            content: 지식 항목 내용
            category: 카테고리 (미제공 시 자동 분류)
            tags: 태그 리스트 (미제공 시 자동 추출)
            source_type: 소스 타입 (manual, file, conversation)
            author: 작성자
            status: 상태 (draft, published)
            
        Returns:
            생성된 KnowledgeEntry 객체
        """
        try:
            logger.info(
                "Creating knowledge entry",
                title=title,
                source_type=source_type,
                status=status,
            )
            
            # 1. 태그 자동 추출 (미제공 시)
            if not tags:
                tags = await self._extract_tags(content)
            
            # 2. 카테고리 자동 분류 (미제공 시)
            if not category:
                category = await self._classify_category(title, content)
            
            # 3. 벡터 임베딩 생성
            combined_text = f"{title}\n\n{content}"
            chunks = self._split_knowledge(combined_text)
            
            # 4. ChromaDB 저장
            base_metadata = {
                "type": "knowledge",
                "category": category or "other",
                "tags": ", ".join(tags) if tags else "",  # 리스트를 문자열로 변환
                "title": title,
                "source_type": source_type,
            }
            if user_id is not None:
                base_metadata["user_id"] = str(user_id)
            documents = [
                Document(
                    page_content=chunk,
                    metadata=dict(base_metadata),
                )
                for chunk in chunks
            ]
            
            vector_ids = self.embedding_service.add_documents_to_store(
                documents=documents,
                collection_name="knowledge_base",
            )
            
            # 5. PostgreSQL 저장
            entry = KnowledgeEntry(
                title=title,
                content=content,
                category=category,
                tags=tags,
                source_type=source_type,
                author=author,
                status=status,
                collection_name="knowledge_base",
                vector_ids=vector_ids,
                num_chunks=len(chunks),
                user_id=user_id,
            )
            
            db.add(entry)
            db.commit()
            db.refresh(entry)
            
            logger.info(
                "Knowledge entry created successfully",
                entry_id=entry.id,
                title=entry.title,
                category=entry.category,
                num_chunks=len(chunks),
            )
            
            return entry
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating knowledge entry: {str(e)}")
            raise
    
    async def update_knowledge_entry(
        self,
        db: Session,
        entry_id: int,
        title: Optional[str] = None,
        content: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        status: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> KnowledgeEntry:
        """
        지식 항목 업데이트
        
        Args:
            db: 데이터베이스 세션
            entry_id: 지식 항목 ID
            title: 새로운 제목 (선택)
            content: 새로운 내용 (선택)
            category: 새로운 카테고리 (선택)
            tags: 새로운 태그 (선택)
            status: 새로운 상태 (선택)
            
        Returns:
            업데이트된 KnowledgeEntry 객체
        """
        try:
            query = db.query(KnowledgeEntry).filter(KnowledgeEntry.id == entry_id)
            if user_id is not None:
                query = query.filter(KnowledgeEntry.user_id == user_id)
            entry = query.first()
            if not entry:
                raise ValueError(f"Knowledge entry with id {entry_id} not found")
            
            logger.info(f"Updating knowledge entry {entry_id}")
            
            # 기존 벡터 삭제
            if entry.vector_ids:
                self.embedding_service.delete_documents(
                    document_ids=entry.vector_ids,
                    collection_name="knowledge_base",
                )
            
            # 필드 업데이트
            if title is not None:
                entry.title = title
            if content is not None:
                entry.content = content
            if category is not None:
                entry.category = category
            if tags is not None:
                entry.tags = tags
            if status is not None:
                entry.status = status
            
            # 콘텐츠가 변경된 경우 벡터 재생성
            if content is not None or title is not None:
                combined_text = f"{entry.title}\n\n{entry.content}"
                chunks = self._split_knowledge(combined_text)
                
                update_metadata = {
                    "type": "knowledge",
                    "category": entry.category or "other",
                    "tags": ", ".join(entry.tags) if entry.tags else "",  # 리스트를 문자열로 변환
                    "title": entry.title,
                    "source_type": entry.source_type,
                }
                if user_id is not None:
                    update_metadata["user_id"] = str(user_id)
                documents = [
                    Document(
                        page_content=chunk,
                        metadata=dict(update_metadata),
                    )
                    for chunk in chunks
                ]
                
                vector_ids = self.embedding_service.add_documents_to_store(
                    documents=documents,
                    collection_name="knowledge_base",
                )
                
                entry.vector_ids = vector_ids
                entry.num_chunks = len(chunks)
            
            db.commit()
            db.refresh(entry)
            
            logger.info(f"Knowledge entry {entry_id} updated successfully")
            return entry
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating knowledge entry: {str(e)}")
            raise
    
    def delete_knowledge_entry(
        self,
        db: Session,
        entry_id: int,
        user_id: Optional[int] = None,
    ) -> bool:
        """
        지식 항목 삭제
        
        Args:
            db: 데이터베이스 세션
            entry_id: 지식 항목 ID
            
        Returns:
            삭제 성공 여부
        """
        try:
            query = db.query(KnowledgeEntry).filter(KnowledgeEntry.id == entry_id)
            if user_id is not None:
                query = query.filter(KnowledgeEntry.user_id == user_id)
            entry = query.first()
            if not entry:
                raise ValueError(f"Knowledge entry with id {entry_id} not found")
            
            logger.info(f"Deleting knowledge entry {entry_id}")
            
            # ChromaDB에서 벡터 삭제
            if entry.vector_ids:
                self.embedding_service.delete_documents(
                    document_ids=entry.vector_ids,
                    collection_name="knowledge_base",
                )
            
            # PostgreSQL에서 삭제
            db.delete(entry)
            db.commit()
            
            logger.info(f"Knowledge entry {entry_id} deleted successfully")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting knowledge entry: {str(e)}")
            raise
    
    def get_knowledge_entry(
        self,
        db: Session,
        entry_id: int,
        user_id: Optional[int] = None,
    ) -> Optional[KnowledgeEntry]:
        """지식 항목 조회"""
        query = db.query(KnowledgeEntry).filter(KnowledgeEntry.id == entry_id)
        if user_id is not None:
            query = query.filter(KnowledgeEntry.user_id == user_id)
        return query.first()
    
    def list_knowledge_entries(
        self,
        db: Session,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
        user_id: Optional[int] = None,
    ) -> List[KnowledgeEntry]:
        """
        지식 항목 목록 조회 (필터링 지원)
        
        Args:
            db: 데이터베이스 세션
            category: 카테고리 필터
            tags: 태그 필터 (OR 조건)
            status: 상태 필터
            skip: 페이지네이션 시작
            limit: 페이지네이션 크기
            
        Returns:
            지식 항목 리스트
        """
        query = db.query(KnowledgeEntry)
        
        if user_id is not None:
            query = query.filter(KnowledgeEntry.user_id == user_id)
        
        if category:
            query = query.filter(KnowledgeEntry.category == category)
        
        if status:
            query = query.filter(KnowledgeEntry.status == status)
        
        if tags:
            # JSON 배열에서 태그 검색
            for tag in tags:
                query = query.filter(KnowledgeEntry.tags.contains([tag]))
        
        return query.order_by(KnowledgeEntry.created_at.desc()).offset(skip).limit(limit).all()
    
    async def extract_knowledge_from_file(
        self,
        db: Session,
        file_content: str,
        file_name: str,
        file_type: str,
        author: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> KnowledgeEntry:
        """
        파일에서 지식 추출 및 등록
        
        Args:
            db: 데이터베이스 세션
            file_content: 파일 내용
            file_name: 파일 이름
            file_type: 파일 타입
            author: 작성자
            
        Returns:
            생성된 KnowledgeEntry 객체
        """
        try:
            logger.info(f"Extracting knowledge from file: {file_name}")
            
            # 마크다운 파일의 경우 제목 추출
            title = file_name
            content = file_content
            
            if file_type == ".md":
                lines = file_content.split("\n")
                for line in lines:
                    if line.startswith("# "):
                        title = line[2:].strip()
                        break
            
            # 지식 항목 생성
            entry = await self.create_knowledge_entry(
                db=db,
                title=title,
                content=content,
                source_type="file",
                author=author,
                status="published",
                user_id=user_id,
            )
            
            logger.info(f"Knowledge extracted from file: {file_name}, entry_id: {entry.id}")
            return entry
            
        except Exception as e:
            logger.error(f"Error extracting knowledge from file: {str(e)}")
            raise
    
    # 카테고리 관리 메서드
    def create_category(
        self,
        db: Session,
        name: str,
        description: Optional[str] = None,
        color: Optional[str] = None,
        icon: Optional[str] = None,
        display_order: int = 0,
    ) -> KnowledgeCategory:
        """카테고리 생성"""
        try:
            category = KnowledgeCategory(
                name=name,
                description=description,
                color=color,
                icon=icon,
                display_order=display_order,
            )
            
            db.add(category)
            db.commit()
            db.refresh(category)
            
            logger.info(f"Category created: {name}")
            return category
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating category: {str(e)}")
            raise
    
    def list_categories(self, db: Session) -> List[KnowledgeCategory]:
        """카테고리 목록 조회"""
        return db.query(KnowledgeCategory).order_by(KnowledgeCategory.display_order).all()
    
    def get_category_by_name(self, db: Session, name: str) -> Optional[KnowledgeCategory]:
        """이름으로 카테고리 조회"""
        return db.query(KnowledgeCategory).filter(KnowledgeCategory.name == name).first()
