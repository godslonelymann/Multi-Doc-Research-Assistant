import SourceList from "./SourceList.jsx";

function CompareSelectionPanel({ documents, selectedIds, onSelect }) {
  const completedDocuments = documents.filter((document) => document.upload_status === "completed");

  return (
    <div className="soft-surface p-5">
      <div className="mb-4 flex items-center justify-between gap-4">
        <div>
          <h3 className="text-sm font-semibold text-[#1d1d1f]">Documents to compare</h3>
          <p className="mt-1 text-sm text-[#6e6e73]">Choose at least two ready sources.</p>
        </div>
        <p className="text-sm font-medium text-[#6e6e73]">{selectedIds.length} selected</p>
      </div>
      <SourceList documents={completedDocuments} selectedIds={selectedIds} onSelect={onSelect} />
    </div>
  );
}

export default CompareSelectionPanel;
