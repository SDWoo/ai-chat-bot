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


class DocumentProcessor:
    def __init__(self):
        self.loaders_map = {
            ".pdf": PyPDFLoader,
            ".docx": Docx2txtLoader,
            ".txt": TextLoader,
            ".md": TextLoader,
            ".csv": CSVLoader,
            ".sql": TextLoader,
        }

    def load_document(self, file_path: str, metadata: Optional[dict] = None) -> List[Document]:
        """Load a document from file path and extract text with metadata."""
        try:
            path = Path(file_path)
            file_extension = path.suffix.lower()

            if file_extension not in self.loaders_map:
                raise ValueError(f"Unsupported file type: {file_extension}")

            logger.info(f"Loading document: {file_path}", file_type=file_extension)

            loader_class = self.loaders_map[file_extension]
            
            if file_extension in [".txt", ".md", ".sql"]:
                loader = loader_class(file_path, encoding="utf-8")
            else:
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
            raise ValueError(f"Could not decode file. Please ensure it's a valid UTF-8 encoded text file.")
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
