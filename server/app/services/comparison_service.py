import json
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.comparison_prompts import build_comparison_prompt, build_conflict_prompt
from app.models.document import Document
from app.models.workspace import Workspace
from app.schemas.chat import Citation, SourceChunk
from app.schemas.comparison import (
    CompareRequest,
    CompareResponse,
    ComparisonItem,
    ConflictDetectionRequest,
    ConflictDetectionResponse,
    ConflictItem,
)
from app.services.llm_service import LLMService
from app.services.retrieval_service import RetrievalService
from app.utils.citations import normalize_source_label


DEFAULT_COMPARISON_TOPIC = (
    "comprehensive comparison of the selected documents, including central themes, methods, evidence, "
    "findings, assumptions, limitations, similarities, differences, and conflicts"
)
DEFAULT_CONFLICT_TOPIC = (
    "possible conflicts, disagreements, inconsistent claims, methodological tensions, and unresolved "
    "differences across the selected documents"
)


class ComparisonService:
    def __init__(
        self,
        db: Session,
        retrieval_service: RetrievalService | None = None,
        llm_service: LLMService | None = None,
    ) -> None:
        self.db = db
        self.retrieval_service = retrieval_service or RetrievalService(db)
        self.llm_service = llm_service or LLMService()

    async def compare(self, payload: CompareRequest) -> CompareResponse:
        documents = self._load_documents(payload.workspace_id, payload.document_ids)
        topic = payload.topic or DEFAULT_COMPARISON_TOPIC
        source_chunks, citation_map = await self._retrieve_grouped_context(
            workspace_id=payload.workspace_id,
            documents=documents,
            topic=topic,
            top_k_per_document=payload.top_k_per_document,
        )
        if not source_chunks:
            return CompareResponse(
                summary="No relevant source chunks were found for the selected documents.",
                document_names=[document.original_name for document in documents],
            )

        grouped_context = self._build_grouped_context(documents, source_chunks, citation_map)
        prompt = build_comparison_prompt(topic=topic, grouped_context=grouped_context)
        raw_output = await self.llm_service.generate(prompt)
        parsed = self._parse_json(raw_output)

        return CompareResponse(
            summary=parsed.get("summary") or "Comparison generated from retrieved source chunks.",
            similarities=self._parse_comparison_items(parsed.get("similarities", []), citation_map),
            differences=self._parse_comparison_items(parsed.get("differences", []), citation_map),
            conflicts=self._parse_conflicts(parsed.get("conflicts", []), citation_map),
            source_chunks=source_chunks,
            document_names=[document.original_name for document in documents],
        )

    async def detect_conflicts(self, payload: ConflictDetectionRequest) -> ConflictDetectionResponse:
        documents = self._load_documents(payload.workspace_id, payload.document_ids)
        topic = payload.topic or DEFAULT_CONFLICT_TOPIC
        source_chunks, citation_map = await self._retrieve_grouped_context(
            workspace_id=payload.workspace_id,
            documents=documents,
            topic=topic,
            top_k_per_document=payload.top_k_per_document,
        )
        if not source_chunks:
            return ConflictDetectionResponse(
                summary="No relevant source chunks were found for conflict detection.",
                document_names=[document.original_name for document in documents],
            )

        grouped_context = self._build_grouped_context(documents, source_chunks, citation_map)
        prompt = build_conflict_prompt(topic=topic, grouped_context=grouped_context)
        raw_output = await self.llm_service.generate(prompt)
        parsed = self._parse_json(raw_output)

        return ConflictDetectionResponse(
            summary=parsed.get("summary") or "Conflict detection generated from retrieved source chunks.",
            conflicts=self._parse_conflicts(parsed.get("conflicts", []), citation_map),
            source_chunks=source_chunks,
            document_names=[document.original_name for document in documents],
        )

    def _load_documents(self, workspace_id: int, document_ids: list[int]) -> list[Document]:
        if not self.db.get(Workspace, workspace_id):
            raise LookupError(f"Workspace {workspace_id} was not found")

        unique_ids = list(dict.fromkeys(document_ids))
        if len(unique_ids) < 2:
            raise ValueError("Select at least two distinct documents")

        statement = (
            select(Document)
            .where(Document.workspace_id == workspace_id)
            .where(Document.id.in_(unique_ids))
            .order_by(Document.id.asc())
        )
        documents = list(self.db.scalars(statement).all())
        found_ids = {document.id for document in documents}
        missing_ids = [document_id for document_id in unique_ids if document_id not in found_ids]
        if missing_ids:
            raise LookupError(f"Documents not found in workspace {workspace_id}: {missing_ids}")
        not_ready = [document.original_name for document in documents if document.upload_status != "completed"]
        if not_ready:
            raise ValueError(f"Only completed documents can be compared: {not_ready}")
        return documents

    async def _retrieve_grouped_context(
        self,
        workspace_id: int,
        documents: list[Document],
        topic: str,
        top_k_per_document: int | None,
    ) -> tuple[list[SourceChunk], dict[str, Citation]]:
        source_chunks: list[SourceChunk] = []
        citation_map: dict[str, Citation] = {}

        for document_position, document in enumerate(documents, start=1):
            if hasattr(self.retrieval_service, "retrieve_for_document_async"):
                chunks = await self.retrieval_service.retrieve_for_document_async(
                    workspace_id=workspace_id,
                    document_id=document.id,
                    query=topic,
                    top_k=top_k_per_document,
                )
            else:
                chunks = self.retrieval_service.retrieve_for_document(
                    workspace_id=workspace_id,
                    document_id=document.id,
                    query=topic,
                    top_k=top_k_per_document,
                )
            for chunk_position, chunk in enumerate(chunks, start=1):
                label = f"D{document_position}-S{chunk_position}"
                citation_map[label] = Citation(
                    document_id=chunk.document_id,
                    document_name=chunk.document_name,
                    page_number=chunk.page_number,
                    chunk_index=chunk.chunk_index,
                    source_label=label,
                )
                source_chunks.append(chunk)

        return source_chunks, citation_map

    def _build_grouped_context(
        self,
        documents: list[Document],
        source_chunks: list[SourceChunk],
        citation_map: dict[str, Citation],
    ) -> str:
        labels_by_vector_id = {
            citation.source_label: citation for citation in citation_map.values()
        }
        chunks_by_document: dict[int, list[tuple[str, SourceChunk]]] = defaultdict(list)

        for label, citation in labels_by_vector_id.items():
            matching_chunk = next(
                (
                    chunk
                    for chunk in source_chunks
                    if chunk.document_id == citation.document_id and chunk.chunk_index == citation.chunk_index
                ),
                None,
            )
            if matching_chunk:
                chunks_by_document[citation.document_id].append((label, matching_chunk))

        blocks: list[str] = []
        for index, document in enumerate(documents, start=1):
            blocks.append(f"Document D{index}: {document.original_name} (id={document.id})")
            for label, chunk in chunks_by_document.get(document.id, []):
                page_label = f", page {chunk.page_number}" if chunk.page_number is not None else ""
                blocks.append(f"[{label}] {document.original_name}{page_label}, chunk {chunk.chunk_index}\n{chunk.text}")

        return "\n\n".join(blocks)

    def _parse_json(self, raw_output: str) -> dict:
        cleaned = raw_output.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            return {
                "summary": cleaned,
                "similarities": [],
                "differences": [],
                "conflicts": [],
            }
        return parsed if isinstance(parsed, dict) else {}

    def _parse_comparison_items(self, items: list[dict], citation_map: dict[str, Citation]) -> list[ComparisonItem]:
        parsed_items: list[ComparisonItem] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            parsed_items.append(
                ComparisonItem(
                    point=str(item.get("point", "")),
                    citations=self._resolve_citations(item.get("citations", []), citation_map),
                )
            )
        return parsed_items

    def _parse_conflicts(self, items: list[dict], citation_map: dict[str, Citation]) -> list[ConflictItem]:
        parsed_items: list[ConflictItem] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            parsed_items.append(
                ConflictItem(
                    claim_a=str(item.get("claim_a", "")),
                    citations_a=self._resolve_citations(item.get("citations_a", []), citation_map),
                    claim_b=str(item.get("claim_b", "")),
                    citations_b=self._resolve_citations(item.get("citations_b", []), citation_map),
                    explanation=str(item.get("explanation", "")),
                    confidence=str(item.get("confidence", "low")),
                )
            )
        return parsed_items

    def _resolve_citations(self, labels: list[str], citation_map: dict[str, Citation]) -> list[Citation]:
        normalized_map = {normalize_source_label(label): citation for label, citation in citation_map.items()}
        resolved: list[Citation] = []
        for label in labels:
            normalized = normalize_source_label(label)
            if normalized in normalized_map:
                resolved.append(normalized_map[normalized])
        return resolved
