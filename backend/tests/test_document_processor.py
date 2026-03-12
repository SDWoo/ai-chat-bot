import pytest
from app.services.document_processor import DocumentProcessor
from pathlib import Path
import tempfile
import os


@pytest.fixture
def doc_processor():
    return DocumentProcessor()


@pytest.fixture
def temp_txt_file():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("This is a test document.\n" * 10)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


def test_validate_file_success(doc_processor, temp_txt_file):
    result = doc_processor.validate_file(temp_txt_file)
    assert result is True


def test_validate_file_not_found(doc_processor):
    with pytest.raises(FileNotFoundError):
        doc_processor.validate_file("nonexistent_file.txt")


def test_validate_file_unsupported_type(doc_processor):
    with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as f:
        temp_path = f.name
    
    try:
        with pytest.raises(ValueError, match="File type not allowed"):
            doc_processor.validate_file(temp_path)
    finally:
        os.unlink(temp_path)


def test_load_document_txt(doc_processor, temp_txt_file):
    documents = doc_processor.load_document(temp_txt_file)
    
    assert len(documents) > 0
    assert all(hasattr(doc, 'page_content') for doc in documents)
    assert all(hasattr(doc, 'metadata') for doc in documents)
    assert all('source' in doc.metadata for doc in documents)
    assert all('file_type' in doc.metadata for doc in documents)
