function CitationCard({ citation }) {
  const sourceLabel = citation.source_label || citation.sourceLabel || "Evidence";
  const documentName = citation.document_name || citation.documentName || "Unknown document";
  const pageNumber = citation.page_number ?? citation.pageNumber;
  const chunkIndex = citation.chunk_index ?? citation.chunkIndex;

  return (
    <span className="inline-flex max-w-full items-center rounded-md border border-[#d2d2d7] bg-[#fbfbfd] px-2 py-1 text-xs font-medium text-[#424245]">
      <span className="truncate">
        {sourceLabel}: {documentName}
        {pageNumber ? `, p. ${pageNumber}` : ""}
        {chunkIndex !== undefined ? `, chunk ${chunkIndex}` : ""}
      </span>
    </span>
  );
}

export default CitationCard;
