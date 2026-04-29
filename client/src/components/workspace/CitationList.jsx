import CitationCard from "../research/CitationCard.jsx";

function CitationList({ citations = [] }) {
  if (!citations.length) {
    return null;
  }

  return (
    <div className="mt-4 flex flex-wrap gap-2" aria-label="Citations">
      {citations.map((citation, index) => (
        <CitationCard
          key={`${citation.source_label || citation.document_name || "citation"}-${index}`}
          citation={citation}
        />
      ))}
    </div>
  );
}

export default CitationList;
