function SourceList({ documents = [], selectedIds = [], onSelect, onDelete, deletingId }) {
  const statusText = {
    completed: "Ready",
    processing: "Processing",
    failed: "Needs attention",
    pending: "Pending",
  };

  if (!documents.length) {
    return (
      <div className="rounded-lg border border-dashed border-[#d2d2d7] bg-[#fbfbfd] p-4">
        <h3 className="text-sm font-semibold text-[#1d1d1f]">No sources yet</h3>
        <p className="mt-2 text-sm leading-6 text-[#6e6e73]">Upload PDFs or text files to start asking grounded questions.</p>
      </div>
    );
  }

  return (
    <div className="divide-y divide-[#e8e8ed]">
      {documents.map((document) => {
        const selected = selectedIds.includes(document.id);
        return (
          <article
            key={document.id}
            className={[
              "py-3 first:pt-0 last:pb-0",
              selected ? "text-[#1d1d1f]" : "",
            ].join(" ")}
          >
            <div className="flex items-start gap-3">
              {onSelect ? (
                <input
                  type="checkbox"
                  checked={selected}
                  onChange={(event) => onSelect(document.id, event.target.checked)}
                  disabled={document.upload_status !== "completed"}
                  className="mt-1 h-4 w-4 rounded border-[#d2d2d7] text-[#0071e3] focus:ring-[#0071e3]/20 disabled:opacity-40"
                />
              ) : null}
              <div className="min-w-0 flex-1">
                <h3 className="truncate text-sm font-semibold text-[#1d1d1f]">{document.original_name}</h3>
                <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-xs text-[#86868b]">
                  <span>{document.file_type?.toUpperCase()}</span>
                  <span>{document.chunk_count ?? 0} chunks</span>
                  <span className={document.upload_status === "failed" ? "text-[#ff3b30]" : "text-[#424245]"}>
                    {statusText[document.upload_status] || document.upload_status}
                  </span>
                </div>
                {document.error_message ? <p className="mt-2 text-xs leading-5 text-[#b42318]">{document.error_message}</p> : null}
              </div>
              {onDelete ? (
                <button
                  type="button"
                  onClick={() => onDelete(document.id)}
                  disabled={deletingId === document.id}
                  className="quiet-button -mr-2 -mt-2"
                >
                  {deletingId === document.id ? "Deleting" : "Remove"}
                </button>
              ) : null}
            </div>
          </article>
        );
      })}
    </div>
  );
}

export default SourceList;
