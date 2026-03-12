import pytest
from app.services.chunking import ChunkingService
from langchain.schema import Document


@pytest.fixture
def chunking_service():
    return ChunkingService(chunk_size=100, chunk_overlap=20)


def test_chunk_documents(chunking_service):
    documents = [
        Document(
            page_content="This is a test document. " * 50,
            metadata={"source": "test.txt"}
        )
    ]
    
    chunks = chunking_service.chunk_documents(documents)
    
    assert len(chunks) > 1
    assert all(hasattr(chunk, 'page_content') for chunk in chunks)
    assert all(hasattr(chunk, 'metadata') for chunk in chunks)
    assert all('chunk_index' in chunk.metadata for chunk in chunks)


def test_chunk_text(chunking_service):
    text = "This is a long test text. " * 50
    
    chunks = chunking_service.chunk_text(text, metadata={"source": "test"})
    
    assert len(chunks) > 0
    assert all(chunk.metadata.get("source") == "test" for chunk in chunks)


def test_chunk_overlap(chunking_service):
    text = "Word " * 100
    chunks = chunking_service.chunk_text(text)
    
    if len(chunks) > 1:
        first_chunk_end = chunks[0].page_content[-20:]
        second_chunk_start = chunks[1].page_content[:20]
        assert any(word in second_chunk_start for word in first_chunk_end.split())


def test_get_optimal_chunk_params(chunking_service):
    documents = [
        Document(page_content="Test document " * 100, metadata={})
        for _ in range(5)
    ]
    
    params = chunking_service.get_optimal_chunk_params(documents)
    
    assert "total_documents" in params
    assert "suggested_chunk_size" in params
    assert "suggested_overlap" in params
    assert params["total_documents"] == 5


def test_chunk_documents_with_document_id(chunking_service):
    """document_id 전달 시 chunk_id에 포함되어 삭제 추적 가능"""
    documents = [
        Document(
            page_content="This is a test document. " * 50,
            metadata={"source": "test.txt", "file_type": ".txt"}
        )
    ]
    
    chunks = chunking_service.chunk_documents(documents, document_id=123)
    
    assert len(chunks) > 1
    for chunk in chunks:
        assert chunk.metadata["chunk_id"].startswith("doc_123_")
        assert chunk.metadata.get("document_id") == "123"
