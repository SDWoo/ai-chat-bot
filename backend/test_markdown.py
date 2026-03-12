"""
Markdown 파일 처리 테스트 스크립트
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from app.services.document_processor import DocumentProcessor
from app.services.chunking import ChunkingService


def create_test_markdown():
    """테스트용 Markdown 파일 생성"""
    test_content = """# Markdown 테스트 문서

## 소개
이것은 Markdown 파일 처리를 테스트하기 위한 문서입니다.

## 섹션 1: 기본 텍스트
여기는 일반적인 텍스트입니다. 
여러 줄에 걸쳐 있는 문장들이 포함되어 있습니다.

### 하위 섹션 1.1
- 리스트 항목 1
- 리스트 항목 2
- 리스트 항목 3

## 섹션 2: 코드 예제

```python
def hello_world():
    print("Hello, World!")
```

## 섹션 3: 긴 문단
Lorem ipsum dolor sit amet, consectetur adipiscing elit. 
Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. 
Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris.

## 결론
Markdown 파일 처리가 정상적으로 작동해야 합니다.
"""
    
    test_file = Path("test_document.md")
    test_file.write_text(test_content, encoding="utf-8")
    return str(test_file)


def test_markdown_processing():
    """Markdown 파일 처리 테스트"""
    print("=" * 60)
    print("Markdown 파일 처리 테스트 시작")
    print("=" * 60)
    
    try:
        # 테스트 파일 생성
        print("\n1. 테스트 Markdown 파일 생성 중...")
        test_file = create_test_markdown()
        print(f"   ✓ 파일 생성 완료: {test_file}")
        
        # 문서 로더 테스트
        print("\n2. DocumentProcessor로 파일 로드 중...")
        processor = DocumentProcessor()
        documents = processor.load_document(test_file)
        print(f"   ✓ 문서 로드 완료: {len(documents)}개 문서")
        print(f"   - 내용 길이: {len(documents[0].page_content)} 문자")
        print(f"   - 메타데이터: {documents[0].metadata}")
        
        # 청킹 테스트
        print("\n3. ChunkingService로 청킹 중...")
        chunker = ChunkingService(chunk_size=500, chunk_overlap=100)
        chunks = chunker.chunk_documents(documents)
        print(f"   ✓ 청킹 완료: {len(chunks)}개 청크")
        
        # 청크 상세 정보
        print("\n4. 청크 상세 정보:")
        for i, chunk in enumerate(chunks[:3]):  # 처음 3개만 표시
            print(f"\n   청크 {i+1}:")
            print(f"   - 내용 미리보기: {chunk.page_content[:100]}...")
            print(f"   - 토큰 수: {chunk.metadata.get('chunk_size', 'N/A')}")
            print(f"   - 청크 ID: {chunk.metadata.get('chunk_id', 'N/A')}")
        
        print("\n" + "=" * 60)
        print("✓ 모든 테스트 통과!")
        print("=" * 60)
        
        # 테스트 파일 정리
        Path(test_file).unlink()
        print(f"\n✓ 테스트 파일 삭제 완료: {test_file}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_markdown_processing()
    sys.exit(0 if success else 1)
