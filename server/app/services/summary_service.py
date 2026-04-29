from sqlalchemy.orm import Session

from app.ai.synthesis_prompts import build_summary_prompt
from app.core.config import settings
from app.models.summary import Summary
from app.models.workspace import Workspace
from app.schemas.chat import Citation
from app.schemas.summary import SummaryGenerateRequest, SummaryKeyPoint
from app.services.context_builder import ContextBuilder
from app.services.llm_service import LLMService
from app.services.retrieval_service import RetrievalService
from app.services.synthesis_parser import SynthesisParser


DEFAULT_SUMMARY_TOPIC = (
    "comprehensive high-level synthesis of all uploaded sources, including central themes, evidence, "
    "findings, methods, limitations, agreements, disagreements, and open questions"
)
SUMMARY_DISPLAY_TOPIC = "Workspace synthesis"


class SummaryService:
    def __init__(
        self,
        db: Session,
        retrieval_service: RetrievalService | None = None,
        llm_service: LLMService | None = None,
        context_builder: ContextBuilder | None = None,
        parser: SynthesisParser | None = None,
    ) -> None:
        self.db = db
        self.retrieval_service = retrieval_service or RetrievalService(db)
        self.llm_service = llm_service or LLMService()
        self.context_builder = context_builder or ContextBuilder()
        self.parser = parser or SynthesisParser()

    async def generate(self, payload: SummaryGenerateRequest) -> Summary:
        if not self.db.get(Workspace, payload.workspace_id):
            raise LookupError(f"Workspace {payload.workspace_id} was not found")

        topic = payload.topic or DEFAULT_SUMMARY_TOPIC
        if hasattr(self.retrieval_service, "retrieve_async"):
            source_chunks = await self.retrieval_service.retrieve_async(
                workspace_id=payload.workspace_id,
                question=topic,
                top_k=payload.top_k or settings.summary_top_k,
            )
        else:
            source_chunks = self.retrieval_service.retrieve(
                workspace_id=payload.workspace_id,
                question=topic,
                top_k=payload.top_k or settings.summary_top_k,
            )
        context, citations = self.context_builder.build(source_chunks)
        citation_map = {citation.source_label: citation for citation in citations}

        if not source_chunks:
            summary_text = "No relevant source chunks were found for this topic."
            key_points: list[SummaryKeyPoint] = []
            resolved_citations: list[Citation] = []
        else:
            raw_output = await self.llm_service.generate(build_summary_prompt(topic=topic, context=context))
            parsed = self.parser.parse_json_object(raw_output)
            summary_text = str(parsed.get("summary") or raw_output).strip()
            key_points = self._parse_key_points(parsed.get("key_points", []), citation_map)
            resolved_citations = self._unique_citations(
                [citation for point in key_points for citation in point.citations]
            )

        summary = Summary(
            workspace_id=payload.workspace_id,
            topic=payload.topic or SUMMARY_DISPLAY_TOPIC,
            summary=summary_text,
            key_points=[point.model_dump() for point in key_points],
            citations=self.parser.citation_dicts(resolved_citations),
            source_chunks=[chunk.model_dump() for chunk in source_chunks],
        )
        self.db.add(summary)
        self.db.commit()
        self.db.refresh(summary)
        return summary

    def get_summary(self, summary_id: int) -> Summary | None:
        return self.db.get(Summary, summary_id)

    def _parse_key_points(self, items: list[dict], citation_map: dict[str, Citation]) -> list[SummaryKeyPoint]:
        key_points: list[SummaryKeyPoint] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            key_points.append(
                SummaryKeyPoint(
                    point=str(item.get("point", "")),
                    citations=self.parser.resolve_citations(item.get("citations", []), citation_map),
                )
            )
        return key_points

    def _unique_citations(self, citations: list[Citation]) -> list[Citation]:
        seen: set[str] = set()
        unique: list[Citation] = []
        for citation in citations:
            key = f"{citation.document_id}:{citation.page_number}:{citation.chunk_index}:{citation.source_label}"
            if key not in seen:
                seen.add(key)
                unique.append(citation)
        return unique
