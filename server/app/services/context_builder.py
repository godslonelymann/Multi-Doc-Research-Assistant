from app.schemas.chat import Citation, SourceChunk


class ContextBuilder:
    def build(self, source_chunks: list[SourceChunk]) -> tuple[str, list[Citation]]:
        context_blocks: list[str] = []
        citations: list[Citation] = []

        for index, chunk in enumerate(source_chunks, start=1):
            source_label = f"Evidence {index}"
            page_label = f", page {chunk.page_number}" if chunk.page_number is not None else ""
            context_blocks.append(
                "\n".join(
                    [
                        f"[{source_label}] {chunk.document_name}{page_label}, chunk {chunk.chunk_index}",
                        chunk.text,
                    ]
                )
            )
            citations.append(
                Citation(
                    document_id=chunk.document_id,
                    document_name=chunk.document_name,
                    page_number=chunk.page_number,
                    chunk_index=chunk.chunk_index,
                    source_label=source_label,
                )
            )

        return "\n\n".join(context_blocks), citations
