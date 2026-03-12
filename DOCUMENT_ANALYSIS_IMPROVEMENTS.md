# 문서 분석 및 벡터 DB 개선 사항

## 개요

RAG 시스템의 문서 분석 파이프라인과 벡터 DB 저장 구조를 최적화했습니다.

---

## 1. 청킹 전략 개선

### 변경 사항

| 항목 | 기존 | 개선 |
|------|------|------|
| **오버랩** | 150 (약 19%) | 160 (20%) - 경계 손실 완화 |
| **분리자** | `\n\n`, `\n`, `. `, ` ` | `\n## `, `\n# `, `\n\n`, `\n`, `. `, ` ` - 구조 인식 |
| **chunk_id** | source_docIdx_chunkIdx | doc_{document_id}_{docIdx}_{chunkIdx} - 삭제 추적 |

### 구조 인식 분리자

- **Markdown/구조화 문서**: `##`, `#` 헤더를 우선 분리하여 섹션 단위 유지
- **일반 텍스트**: 단락 → 문장 → 단어 순으로 자연 경계 유지
- **권장 청크 크기**: 512~1024 토큰, 10~20% 오버랩

---

## 2. 벡터 DB 저장 구조 개선

### document_id 기반 추적

- 청크 메타데이터에 `document_id` 추가
- `chunk_id` 형식: `doc_{document_id}_{page_idx}_{chunk_idx}`
- 문서 삭제 시 해당 문서의 모든 벡터 정확히 삭제

### vector_ids 컬럼 추가

- `documents` 테이블에 `vector_ids` (JSON) 컬럼 추가
- ChromaDB에 저장된 청크 ID 목록 보관
- 문서 삭제 시 `vector_ids`를 사용해 ChromaDB에서 일괄 삭제

### ChromaDB 메타데이터 정규화

- ChromaDB는 str/int/float/bool만 허용
- datetime, None 등은 자동 변환하여 저장

---

## 3. 문서 삭제 시 ChromaDB 정리

### 기존 문제

- 문서 삭제 시 PostgreSQL과 로컬 파일만 삭제
- ChromaDB 벡터는 그대로 남아 오프된 벡터 누적

### 개선 내용

- 문서 삭제 시 `vector_ids`에 저장된 ID로 ChromaDB에서 해당 벡터 삭제
- DB, 파일, 벡터 저장소가 동일한 문서 기준으로 정리됨

---

## 4. 마이그레이션

```bash
alembic upgrade head
```

- `003_add_document_vector_ids.py`: `documents.vector_ids` 컬럼 추가

---

## 5. 테스트

```bash
# 청킹 테스트
pytest tests/test_chunking.py -v

# 통합 테스트
python test_auth.py
```

---

## 6. 향후 개선 가능 영역

1. **시맨틱 청킹**: 임베딩 기반 주제 경계 탐지 (품질 10~20% 향상, 비용 증가)
2. **계층적 청킹**: 작은 청크로 검색, 큰 부모 청크로 컨텍스트 제공
3. **파일 타입별 전략**: PDF 페이지, DOCX 섹션 등 포맷별 최적화
