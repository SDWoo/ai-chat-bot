from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    CSVLoader,
)
from langchain.schema import Document
from pathlib import Path
from typing import List, Optional
import structlog
from datetime import datetime

from app.core.config import settings

logger = structlog.get_logger()

# 텍스트 파일 인코딩 시도 순서 (한글 Windows/Oracle 환경 대응)
TEXT_ENCODINGS = ["utf-8", "utf-8-sig", "euc-kr", "cp949", "latin-1"]


class DocumentProcessor:
    def __init__(self):
        self.loaders_map = {
            ".pdf": PyPDFLoader,
            ".docx": Docx2txtLoader,
            ".txt": TextLoader,
            ".md": TextLoader,
            ".csv": CSVLoader,
            ".sql": TextLoader,
            ".tst": TextLoader,
        }

    def _load_text_with_fallback(self, file_path: str) -> List[Document]:
        """여러 인코딩을 시도해서 텍스트 파일을 로드"""
        last_error = None
        for enc in TEXT_ENCODINGS:
            try:
                loader = TextLoader(file_path, encoding=enc)
                docs = loader.load()
                if docs and docs[0].page_content.strip():
                    logger.info(f"Loaded with encoding: {enc}", file_path=file_path)
                    return docs
            except Exception as e:
                last_error = e
                continue

        # 모든 인코딩 실패 → 바이너리로 읽어서 디코딩
        try:
            raw = Path(file_path).read_bytes()
            for enc in TEXT_ENCODINGS:
                try:
                    text = raw.decode(enc)
                    if text.strip():
                        logger.info(f"Loaded via raw bytes with encoding: {enc}", file_path=file_path)
                        return [Document(page_content=text, metadata={"source": str(Path(file_path).name)})]
                except (UnicodeDecodeError, LookupError):
                    continue
        except Exception:
            pass

        raise ValueError(f"Could not decode file with any encoding ({', '.join(TEXT_ENCODINGS)}). Last error: {last_error}")

    def load_document(self, file_path: str, metadata: Optional[dict] = None) -> List[Document]:
        """Load a document from file path and extract text with metadata."""
        try:
            path = Path(file_path)
            file_extension = path.suffix.lower()

            if file_extension not in self.loaders_map:
                raise ValueError(f"Unsupported file type: {file_extension}")

            logger.info(f"Loading document: {file_path}", file_type=file_extension)

            text_extensions = {".txt", ".md", ".sql", ".tst"}
            if file_extension in text_extensions:
                documents = self._load_text_with_fallback(file_path)
            else:
                loader_class = self.loaders_map[file_extension]
                loader = loader_class(file_path)
                documents = loader.load()

            if not documents or not documents[0].page_content.strip():
                raise ValueError(f"Document is empty or could not be loaded: {file_path}")

            additional_metadata = {
                "source": str(path.name),
                "file_path": file_path,
                "file_type": file_extension,
                "loaded_at": datetime.utcnow().isoformat(),
            }

            if metadata:
                additional_metadata.update(metadata)

            for doc in documents:
                doc.metadata.update(additional_metadata)

            logger.info(
                f"Successfully loaded document",
                file=file_path,
                num_documents=len(documents),
            )

            return documents

        except UnicodeDecodeError as e:
            logger.error(f"Encoding error loading document: {str(e)}", file_path=file_path)
            raise ValueError(f"Could not decode file with any supported encoding.")
        except Exception as e:
            logger.error(f"Error loading document: {str(e)}", file_path=file_path)
            raise

    def validate_file(self, file_path: str, max_size_mb: Optional[int] = None) -> bool:
        """Validate file size and extension."""
        try:
            path = Path(file_path)

            if not path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            file_extension = path.suffix.lower().replace(".", "")
            if file_extension not in settings.ALLOWED_EXTENSIONS:
                raise ValueError(
                    f"File type not allowed. Supported types: {', '.join(settings.ALLOWED_EXTENSIONS)}"
                )

            max_size = max_size_mb or settings.MAX_FILE_SIZE_MB
            file_size_mb = path.stat().st_size / (1024 * 1024)
            if file_size_mb > max_size:
                raise ValueError(f"File size ({file_size_mb:.2f}MB) exceeds limit ({max_size}MB)")

            return True

        except Exception as e:
            logger.error(f"File validation failed: {str(e)}", file_path=file_path)
            raise
