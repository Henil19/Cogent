"""
Layer 3 Pipeline Orchestrator
Connects Sub-Modules 3.1 - 3.5 into an end-to-end Pre-Retrieval Grounding Pipeline.
Accepts Layer 2 KnowledgeRetrievalPlan and produces Layer 4 AcquiredCorpusBatch.

Research Basis:
- PIC (ACL Findings 2025) & Max-Min Semantic Chunking (Discover Computing 2025)
- SCAN (ACL/EACL 2025/2026) & TechDocRAG (AI 2026)
- IEEE Access (2025) Main Content Extraction
- TROVE (ACL 2025) & Provenance (EMNLP 2024) Lineage Attributions
- Late Chunking (2024/2025) Contextual Headers
- Acquisition Quality Gating (KDD 2024/2025)
"""

import os
import re
import time
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.schemas.layer2 import KnowledgeRetrievalPlan, SourceTarget
from app.schemas.layer3 import (
    SourceType,
    AcquisitionStatus,
    DocumentMetadata,
    AcquiredDocumentChunk,
    AcquiredCorpusBatch,
    DocumentUploadResponse,
)
from app.core.layer3.ingestion.hash_manager import HashManager
from app.core.layer3.ingestion.document_manager import DocumentManager
from app.core.layer3.validation.integrity_validator import IntegrityValidator
from app.core.layer3.validation.quality_checker import QualityChecker
from app.core.layer3.extraction.pdf_extractor import PDFExtractor, ExtractedDocumentUnit
from app.core.layer3.extraction.txt_extractor import TxtExtractor
from app.core.layer3.processing.normalizer import ContentNormalizer
from app.core.layer3.processing.chunker import StructurePreservingChunker
from app.core.layer3.provenance.provenance_manager import ProvenanceManager
from app.core.layer3.acquisition.web_acquisition import WebAcquisitionAdapter
from app.models.document import Document, DocumentChunk


class Layer3Pipeline:
    """
    Orchestrates ingestion, structural extraction, cleaning, chunking,
    and fine-grained provenance attachment.
    Strictly outputs AcquiredCorpusBatch ready for Layer 4 retrieval.
    """

    def __init__(
        self,
        upload_dir: Optional[str] = None,
        target_tokens: int = 512,
        overlap_tokens: int = 64,
        timeout_sec: float = 3.5,
        test_mode: Optional[bool] = None,
    ):
        self.doc_manager = DocumentManager(upload_dir=upload_dir)
        self.pdf_extractor = PDFExtractor()
        self.txt_extractor = TxtExtractor()
        self.chunker = StructurePreservingChunker(
            target_tokens=target_tokens, overlap_tokens=overlap_tokens
        )
        self.web_adapter = WebAcquisitionAdapter(timeout_sec=timeout_sec, test_mode=test_mode)

    def process_file_bytes(
        self,
        filename: str,
        file_bytes: bytes,
        document_id: Optional[str] = None,
        user_id: Optional[str] = None,
        source_uri: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process single document bytes through validation, extraction, cleaning,
        semantic chunking, and provenance attachment.
        """
        # 1. Validation
        is_valid, validation_msg, source_type = IntegrityValidator.validate_bytes(
            file_bytes, filename
        )
        if not is_valid:
            return {
                "success": False,
                "error": validation_msg,
                "chunks": [],
                "metadata": None,
            }

        if source_type is None:
            return {
                "success": False,
                "error": f"Could not determine source type for {filename}.",
                "chunks": [],
                "metadata": None,
            }

        doc_id = document_id or f"doc_{uuid.uuid4().hex[:12]}"
        doc_hash = HashManager.hash_bytes(file_bytes)
        uri = source_uri or filename

        # 2. Structural Extraction
        units: List[ExtractedDocumentUnit] = []
        page_count = 1
        if source_type == SourceType.LOCAL_PDF:
            units = self.pdf_extractor.extract_from_bytes(file_bytes, doc_title=filename)
            if units:
                page_count = max(u.page_number for u in units)
        else:
            try:
                text_content = file_bytes.decode("utf-8")
            except UnicodeDecodeError:
                text_content = file_bytes.decode("latin-1", errors="replace")
            units = self.txt_extractor.extract_from_text(text_content, doc_title=filename)

        if not units:
            return {
                "success": False,
                "error": f"No extractable text or content found in {filename}.",
                "chunks": [],
                "metadata": None,
            }

        # 3. Content Normalization
        for unit in units:
            unit.content = ContentNormalizer.normalize_text(unit.content)

        units = [u for u in units if len(u.content.strip()) > 0]
        if not units:
            return {
                "success": False,
                "error": f"Extracted content in {filename} became empty after normalization.",
                "chunks": [],
                "metadata": None,
            }

        # 4. Semantic Chunking (PIC + Max-Min + Late Chunking)
        raw_chunks = self.chunker.chunk_document_units(units, doc_title=filename)

        # 5. Provenance Attachment (TROVE ACL'25)
        now_iso = datetime.now(timezone.utc).isoformat()
        chunks: List[AcquiredDocumentChunk] = []
        for raw_chk in raw_chunks:
            chunk = ProvenanceManager.attach_provenance(
                raw_chunk=raw_chk,
                document_id=doc_id,
                document_hash=doc_hash,
                title=filename,
                source_type=source_type,
                source_uri=uri,
                author=None,
                publication_date=None,
                retrieved_at=now_iso,
            )
            chunks.append(chunk)

        # Quality diagnostics summary
        avg_quality = (
            sum(c.extraction_quality for c in chunks) / len(chunks) if chunks else 0.0
        )
        section_titles = list({u.section_title for u in units if u.section_title})

        doc_meta = DocumentMetadata(
            document_id=doc_id,
            title=filename,
            source_uri=uri,
            source_type=source_type,
            retrieved_at=now_iso,
            document_hash=doc_hash,
            file_size_bytes=len(file_bytes),
            page_count=page_count,
            section_count=len(section_titles),
            language="en",
            extraction_quality=round(avg_quality, 3),
            processing_warnings=[
                w for c in chunks for w in c.processing_warnings if w
            ][:5],
        )

        return {
            "success": True,
            "document_id": doc_id,
            "doc_hash": doc_hash,
            "source_type": source_type,
            "chunks": chunks,
            "metadata": doc_meta,
        }

    def process_uploaded_document(
        self,
        filename: str,
        file_bytes: bytes,
        user_id: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> DocumentUploadResponse:
        """
        Public endpoint workflow: ingests file, stores on disk/DB, extracts,
        chunks, and returns DocumentUploadResponse.
        """
        # Ingest & persist
        ingest_res = self.doc_manager.ingest_document(
            filename=filename,
            file_bytes=file_bytes,
            user_id=user_id,
            db=db,
        )

        # Process through extraction and chunking
        proc_res = self.process_file_bytes(
            filename=filename,
            file_bytes=file_bytes,
            document_id=ingest_res["document_id"],
            user_id=user_id,
            source_uri=ingest_res.get("file_path", filename),
        )

        if not proc_res["success"]:
            return DocumentUploadResponse(
                document_id=ingest_res["document_id"],
                filename=filename,
                source_type=ingest_res["source_type"],
                file_size_bytes=len(file_bytes),
                document_hash=ingest_res["document_hash"],
                status=AcquisitionStatus.FAILED_EXTRACTION,
                total_chunks=0,
                extraction_quality=0.0,
                message=f"Ingested but extraction failed: {proc_res['error']}",
            )

        # Update DB document status and persist chunks if session present
        if db and ingest_res.get("document_id"):
            try:
                db_doc = (
                    db.query(Document)
                    .filter(Document.id == ingest_res["document_id"])
                    .first()
                )
                if db_doc:
                    db_doc.status = AcquisitionStatus.READY_FOR_RETRIEVAL.value
                    db_doc.chunk_count = len(proc_res["chunks"])
                    db_doc.total_characters = sum(
                        c.char_count for c in proc_res["chunks"]
                    )
                    db.query(DocumentChunk).filter(DocumentChunk.document_id == db_doc.id).delete()
                    for c in proc_res["chunks"]:
                        chunk_row = DocumentChunk(
                            id=c.chunk_id,
                            document_id=db_doc.id,
                            chunk_index=c.chunk_index,
                            content=c.content,
                            content_length=c.char_count,
                            page_number=c.page_number,
                            section_header=c.section_title,
                            metadata_json={
                                "source_type": str(c.source_type.value) if hasattr(c.source_type, "value") else str(c.source_type),
                                "content_hash": c.content_hash,
                                "document_hash": c.document_hash,
                                "token_count": c.token_count_estimate,
                            },
                        )
                        db.add(chunk_row)
                    db.commit()
            except Exception:
                db.rollback()

        meta: DocumentMetadata = proc_res["metadata"]
        return DocumentUploadResponse(
            document_id=ingest_res["document_id"],
            filename=filename,
            source_type=ingest_res["source_type"],
            file_size_bytes=len(file_bytes),
            document_hash=ingest_res["document_hash"],
            status=AcquisitionStatus.READY_FOR_RETRIEVAL,
            total_chunks=len(proc_res["chunks"]),
            extraction_quality=meta.extraction_quality,
            message="Document successfully ingested, structurally extracted, and chunked with provenance.",
        )

    def execute_plan(
        self,
        plan: KnowledgeRetrievalPlan,
        custom_documents: Optional[List[Dict[str, Any]]] = None,
        db: Optional[Session] = None,
    ) -> AcquiredCorpusBatch:
        """
        Execute pre-retrieval acquisition for a Layer 2 KnowledgeRetrievalPlan.
        Acquires local and live web knowledge, transforms into AcquiredDocumentChunk items,
        and packages into AcquiredCorpusBatch for Layer 4.
        """
        t0 = time.perf_counter()
        all_chunks: List[AcquiredDocumentChunk] = []
        documents_metadata: List[DocumentMetadata] = []
        rejected_documents: List[Dict[str, Any]] = []
        processed_hashes = set()

        needed_sources = set(plan.target_sources_summary)
        for sq in plan.sub_queries:
            needed_sources.add(sq.target_source)

        requires_local = (
            SourceTarget.LOCAL_DOCS in needed_sources
            or SourceTarget.HYBRID in needed_sources
        )
        requires_web = (
            SourceTarget.LIVE_WEB in needed_sources
            or SourceTarget.HYBRID in needed_sources
        )

        # -------------------------------------------------------------
        # Part A: Local Document Acquisition & Extraction
        # -------------------------------------------------------------
        if requires_local or custom_documents:
            # 1. Check custom documents passed in request
            if custom_documents:
                for item in custom_documents:
                    fname = item.get("filename", "custom_doc.txt")
                    fbytes = item.get("file_bytes")
                    if isinstance(fbytes, str):
                        fbytes = fbytes.encode("utf-8")
                    if not fbytes:
                        continue

                    doc_hash = HashManager.hash_bytes(fbytes)
                    if doc_hash in processed_hashes:
                        continue

                    res = self.process_file_bytes(fname, fbytes, source_uri=item.get("source_uri"))
                    if res["success"]:
                        all_chunks.extend(res["chunks"])
                        documents_metadata.append(res["metadata"])
                        processed_hashes.add(doc_hash)
                    else:
                        rejected_documents.append({"filename": fname, "reason": res["error"]})

            # 2. Check local disk upload directory
            if os.path.exists(self.doc_manager.upload_dir):
                for fname in os.listdir(self.doc_manager.upload_dir):
                    fpath = os.path.join(self.doc_manager.upload_dir, fname)
                    if not os.path.isfile(fpath):
                        continue
                    _, ext = os.path.splitext(fname.lower())
                    if ext not in self.doc_manager.ALLOWED_EXTENSIONS:
                        continue

                    try:
                        with open(fpath, "rb") as f:
                            fbytes = f.read()
                        doc_hash = HashManager.hash_bytes(fbytes)
                        if doc_hash in processed_hashes:
                            continue

                        res = self.process_file_bytes(fname, fbytes, source_uri=fpath)
                        if res["success"]:
                            all_chunks.extend(res["chunks"])
                            documents_metadata.append(res["metadata"])
                            processed_hashes.add(doc_hash)
                        else:
                            rejected_documents.append({"filename": fname, "reason": res["error"]})
                    except Exception as ex:
                        rejected_documents.append({"filename": fname, "reason": str(ex)})

        # -------------------------------------------------------------
        # Part B: Targeted Live Web / Preprint Acquisition
        # -------------------------------------------------------------
        if requires_web:
            web_subqueries = [
                sq for sq in plan.sub_queries
                if sq.target_source in (SourceTarget.LIVE_WEB, SourceTarget.HYBRID)
            ]
            # If no subqueries specifically tagged but web was requested, use parent query
            if not web_subqueries and requires_web:
                query_text = plan.parent_query
                web_targets = self.web_adapter.acquire_for_subquery(query_text, "LIVE_WEB")
                self._process_web_targets(web_targets, all_chunks, documents_metadata, processed_hashes)
            else:
                for sq in web_subqueries[:4]:
                    web_targets = self.web_adapter.acquire_for_subquery(
                        sq.raw_sub_query, sq.target_source.value
                    )
                    self._process_web_targets(
                        web_targets, all_chunks, documents_metadata, processed_hashes
                    )

        # Fallback: If no documents were acquired yet, query live web on parent query
        if len(all_chunks) == 0 and requires_web:
            query_text = plan.parent_query
            web_targets = self.web_adapter.acquire_for_subquery(query_text, "LIVE_WEB")
            self._process_web_targets(web_targets, all_chunks, documents_metadata, processed_hashes)

        # -------------------------------------------------------------
        # Part C: Assemble AcquiredCorpusBatch for Layer 4
        # -------------------------------------------------------------
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
        batch_status = (
            AcquisitionStatus.READY_FOR_RETRIEVAL
            if all_chunks
            else AcquisitionStatus.DISCOVERED
        )

        return AcquiredCorpusBatch(
            batch_id=f"batch_{uuid.uuid4().hex[:12]}",
            plan_id=plan.plan_id,
            session_id=plan.session_id,
            total_documents=len(documents_metadata),
            total_chunks=len(all_chunks),
            chunks=all_chunks,
            acquisition_time_ms=elapsed_ms,
            status=batch_status,
            documents_metadata=documents_metadata,
            rejected_documents=rejected_documents,
        )

    def _process_web_targets(
        self,
        web_targets: List[Dict[str, Any]],
        all_chunks: List[AcquiredDocumentChunk],
        documents_metadata: List[DocumentMetadata],
        processed_hashes: set,
    ):
        """Process acquired web and preprint payloads into standardized chunks."""
        now_iso = datetime.now(timezone.utc).isoformat()

        for target in web_targets:
            raw_title = target.get("title", "Web Article")
            title = re.sub(r"^\s*\[[\d\.\sA-Za-z\-]+\]\s*", "", raw_title).strip()
            source_uri = target.get("source_uri", "http://external-source")
            author = target.get("author")
            pub_date = target.get("publication_date")
            units: List[ExtractedDocumentUnit] = target.get("units", [])

            if not units:
                continue

            full_text = " ".join(u.content for u in units)
            doc_hash = HashManager.hash_text(full_text)
            if doc_hash in processed_hashes:
                continue

            doc_id = f"doc_web_{uuid.uuid4().hex[:8]}"

            # Semantic chunking
            raw_chunks = self.chunker.chunk_document_units(units, doc_title=title)

            # Provenance
            doc_chunks = []
            for raw_chk in raw_chunks:
                chk = ProvenanceManager.attach_provenance(
                    raw_chunk=raw_chk,
                    document_id=doc_id,
                    document_hash=doc_hash,
                    title=title,
                    source_type=SourceType.LIVE_WEB,
                    source_uri=source_uri,
                    author=author,
                    publication_date=pub_date,
                    retrieved_at=now_iso,
                )
                doc_chunks.append(chk)

            if doc_chunks:
                all_chunks.extend(doc_chunks)
                processed_hashes.add(doc_hash)
                avg_q = sum(c.extraction_quality for c in doc_chunks) / len(doc_chunks)

                documents_metadata.append(
                    DocumentMetadata(
                        document_id=doc_id,
                        title=title,
                        source_uri=source_uri,
                        source_type=SourceType.LIVE_WEB,
                        author=author,
                        publication_date=pub_date,
                        retrieved_at=now_iso,
                        document_hash=doc_hash,
                        file_size_bytes=len(full_text.encode("utf-8")),
                        page_count=1,
                        section_count=len({u.section_title for u in units if u.section_title}),
                        language="en",
                        extraction_quality=round(avg_q, 3),
                        processing_warnings=[],
                    )
                )
