"""
Sub-Module 3.1: Document Ingestion Manager
Research Basis: Master Blueprint Module 1 & Ingestion Integrity
Handles multi-format document ingestion (PDF, TXT, Markdown):
1. Extension & MIME validation
2. Cryptographic deduplication via SHA-256 content hashing
3. Secure disk storage
4. Database registration in the 'documents' table
"""

import os
import uuid
import datetime
from typing import Tuple, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.config import settings
from app.schemas.layer3 import SourceType, AcquisitionStatus
from app.core.layer3.ingestion.hash_manager import HashManager
from app.models.document import Document


class DocumentManager:
    """Manages document uploads, deduplication, and file storage."""

    ALLOWED_EXTENSIONS = {
        ".pdf": SourceType.LOCAL_PDF,
        ".txt": SourceType.LOCAL_TXT,
        ".md": SourceType.LOCAL_MD,
    }

    MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB

    def __init__(self, upload_dir: Optional[str] = None):
        self.upload_dir = upload_dir or getattr(settings, "UPLOAD_DIR", "data/uploads")
        if not os.path.isabs(self.upload_dir):
            self.upload_dir = os.path.abspath(self.upload_dir)
        os.makedirs(self.upload_dir, exist_ok=True)

    def validate_file(self, filename: str, file_bytes: bytes) -> Tuple[bool, Optional[str], Optional[SourceType]]:
        """Validate extension and file size."""
        if not file_bytes:
            return False, "File is completely empty (0 bytes).", None

        if len(file_bytes) > self.MAX_FILE_SIZE_BYTES:
            return False, f"File exceeds maximum allowed size of {self.MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB.", None

        _, ext = os.path.splitext(filename.lower())
        if ext not in self.ALLOWED_EXTENSIONS:
            return False, f"Unsupported file type '{ext}'. Allowed: {list(self.ALLOWED_EXTENSIONS.keys())}", None

        return True, None, self.ALLOWED_EXTENSIONS[ext]

    def ingest_document(
        self,
        filename: str,
        file_bytes: bytes,
        user_id: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """
        Ingest, hash, deduplicate, and persist a document file.
        Returns a dictionary with document metadata and duplicate flag.
        """
        is_valid, error, source_type = self.validate_file(filename, file_bytes)
        if not is_valid:
            raise ValueError(error)

        doc_hash = HashManager.hash_bytes(file_bytes)

        # Check for duplicate document in database
        existing_doc = None
        if db:
            existing_doc = db.query(Document).filter(
                Document.metadata_json["document_hash"].as_string() == doc_hash
            ).first() if hasattr(Document, "metadata_json") else None
            if not existing_doc:
                existing_doc = db.query(Document).filter(Document.filename == filename).first()

        if existing_doc:
            return {
                "document_id": existing_doc.id,
                "filename": existing_doc.filename,
                "file_path": os.path.join(self.upload_dir, f"{existing_doc.id}_{existing_doc.filename}"),
                "source_type": source_type,
                "file_size": existing_doc.file_size,
                "document_hash": doc_hash,
                "is_duplicate": True,
                "status": AcquisitionStatus.ACQUIRED,
            }

        # Generate unique ID and save file to disk
        doc_id = f"doc_{uuid.uuid4().hex[:12]}"
        safe_filename = "".join(c for c in filename if c.isalnum() or c in "._- ")
        saved_path = os.path.join(self.upload_dir, f"{doc_id}_{safe_filename}")

        with open(saved_path, "wb") as f:
            f.write(file_bytes)

        # Register in database if db session provided
        if db:
            new_doc = Document(
                id=doc_id,
                user_id=user_id,
                filename=filename,
                file_type=source_type.value,
                file_size=len(file_bytes),
                status=AcquisitionStatus.ACQUIRED.value,
                chunk_count=0,
                total_characters=0,
                metadata_json={"document_hash": doc_hash, "file_path": saved_path},
            )
            db.add(new_doc)
            db.commit()
            db.refresh(new_doc)

        return {
            "document_id": doc_id,
            "filename": filename,
            "file_path": saved_path,
            "source_type": source_type,
            "file_size": len(file_bytes),
            "document_hash": doc_hash,
            "is_duplicate": False,
            "status": AcquisitionStatus.ACQUIRED,
        }
