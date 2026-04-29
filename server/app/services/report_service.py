from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.ai.synthesis_prompts import build_report_prompt
from app.core.config import settings
from app.models.report import Report
from app.models.report_section import ReportSection
from app.models.workspace import Workspace
from app.schemas.chat import Citation
from app.schemas.report import ReportGenerateRequest
from app.services.context_builder import ContextBuilder
from app.services.llm_service import LLMService
from app.services.retrieval_service import RetrievalService
from app.services.synthesis_parser import SynthesisParser


DEFAULT_REPORT_TOPIC = (
    "comprehensive source-grounded research report across the full workspace, covering major themes, "
    "evidence, findings, methods, limitations, agreements, disagreements, and practical implications"
)


class ReportService:
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

    async def generate(self, payload: ReportGenerateRequest) -> Report:
        if not self.db.get(Workspace, payload.workspace_id):
            raise LookupError(f"Workspace {payload.workspace_id} was not found")

        topic = payload.topic or DEFAULT_REPORT_TOPIC
        if hasattr(self.retrieval_service, "retrieve_async"):
            source_chunks = await self.retrieval_service.retrieve_async(
                workspace_id=payload.workspace_id,
                question=topic,
                top_k=payload.top_k or settings.report_top_k,
            )
        else:
            source_chunks = self.retrieval_service.retrieve(
                workspace_id=payload.workspace_id,
                question=topic,
                top_k=payload.top_k or settings.report_top_k,
            )
        context, citations = self.context_builder.build(source_chunks)
        citation_map = {citation.source_label: citation for citation in citations}

        if not source_chunks:
            report_data = {
                "title": payload.title,
                "introduction": "No relevant source chunks were found for this report topic.",
                "sections": [],
                "conclusion": "No source-grounded conclusion can be generated without relevant retrieved context.",
                "citations": [],
            }
        else:
            raw_output = await self.llm_service.generate(
                build_report_prompt(title=payload.title, topic=topic, context=context)
            )
            report_data = self._validate_report_data(
                parsed=self.parser.parse_json_object(raw_output),
                fallback_title=payload.title,
                fallback_topic=topic,
                fallback_text=raw_output,
                citation_map=citation_map,
            )

        report_citations = self.parser.resolve_citations(report_data.get("citations", []), citation_map)
        report = Report(
            workspace_id=payload.workspace_id,
            title=str(report_data["title"]),
            topic=topic,
            introduction=str(report_data["introduction"]),
            conclusion=str(report_data["conclusion"]),
            citations=self.parser.citation_dicts(report_citations),
            source_chunks=[chunk.model_dump() for chunk in source_chunks],
        )
        self.db.add(report)
        self.db.flush()

        for index, section in enumerate(report_data["sections"]):
            section_citations = self.parser.resolve_citations(section.get("citations", []), citation_map)
            self.db.add(
                ReportSection(
                    report_id=report.id,
                    order_index=index,
                    title=str(section["title"]),
                    content=str(section["content"]),
                    citations=self.parser.citation_dicts(section_citations),
                )
            )

        self.db.commit()
        return self.get_report(report.id) or report

    def get_report(self, report_id: int) -> Report | None:
        statement = select(Report).options(selectinload(Report.sections)).where(Report.id == report_id)
        return self.db.scalar(statement)

    def _validate_report_data(
        self,
        parsed: dict,
        fallback_title: str,
        fallback_topic: str,
        fallback_text: str,
        citation_map: dict[str, Citation],
    ) -> dict:
        title = str(parsed.get("title") or fallback_title).strip()
        introduction = str(parsed.get("introduction") or fallback_text or "").strip()
        conclusion = str(parsed.get("conclusion") or "Conclusion is limited to the retrieved source context.").strip()
        sections = parsed.get("sections", [])
        citations = parsed.get("citations", [])

        valid_sections: list[dict] = []
        if isinstance(sections, list):
            for section in sections:
                if not isinstance(section, dict):
                    continue
                section_title = str(section.get("title") or "").strip()
                content = str(section.get("content") or "").strip()
                if section_title and content:
                    valid_sections.append(
                        {
                            "title": section_title,
                            "content": content,
                            "citations": [
                                citation.source_label
                                for citation in self.parser.resolve_citations(section.get("citations", []), citation_map)
                            ],
                        }
                    )

        if not valid_sections and introduction:
            valid_sections.append(
                {
                    "title": fallback_topic,
                    "content": introduction,
                    "citations": [
                        citation.source_label for citation in self.parser.resolve_citations(citations, citation_map)
                    ],
                }
            )

        return {
            "title": title or fallback_title,
            "introduction": introduction or "Introduction is limited to the retrieved source context.",
            "sections": valid_sections,
            "conclusion": conclusion,
            "citations": [
                citation.source_label for citation in self.parser.resolve_citations(citations, citation_map)
            ],
        }
