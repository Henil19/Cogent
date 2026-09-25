"""
Document Models
Stores uploaded documents and their processed chunks with embeddings.
"""

# pyrefly: ignore [missing-import]
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text, LargeBinary, JSON, func
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import relationship
from app.database import Base
import uuid


class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    filename = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)  # pdf, txt
    file_size = Column(Integer, nullable=False)  # bytes
    status = Column(String(50), default="processing")  # processing, ready, error
    indexing_status = Column(String(50), default="PENDING")  # PENDING, INDEXED, FAILED
    file_path = Column(String(1000), nullable=True)
    error_message = Column(Text, nullable=True)
    chunk_count = Column(Integer, default=0)
    total_characters = Column(Integer, default=0)
    metadata_json = Column(JSON, default=dict)  # extra document metadata
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
    processed_date = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    owner = relationship("User", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Document(id={self.id}, filename={self.filename}, status={self.status})>"


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    content_length = Column(Integer, nullable=False)
    embedding = Column(LargeBinary, nullable=True)  # numpy array serialized
    page_number = Column(Integer, nullable=True)  # source page in document
    section_header = Column(String(500), nullable=True)  # section title if detected
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    document = relationship("Document", back_populates="chunks")

    def __repr__(self):
        return f"<DocumentChunk(id={self.id}, doc={self.document_id}, idx={self.chunk_index})>"
