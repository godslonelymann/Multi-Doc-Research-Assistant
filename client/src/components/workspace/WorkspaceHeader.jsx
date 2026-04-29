function WorkspaceHeader({ workspace, documents = [], onUploadClick }) {
  const completedCount = documents.filter((document) => document.upload_status === "completed").length;
  const processingCount = documents.filter((document) => document.upload_status === "processing").length;
  const failedCount = documents.filter((document) => document.upload_status === "failed").length;

  return (
    <header className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
      <div className="min-w-0">
        <h2 className="text-3xl font-semibold text-[#1d1d1f] sm:text-4xl">{workspace?.name}</h2>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-[#6e6e73] sm:text-base sm:leading-7">
          {workspace?.description || "Upload sources, ask questions, compare evidence, and draft research outputs without leaving this workspace."}
        </p>
      </div>
      <div className="flex shrink-0 items-center gap-3">
        <div className="hidden rounded-lg border border-[#d2d2d7] bg-white/80 px-4 py-3 text-sm text-[#6e6e73] sm:block">
          <div>
            <span className="font-semibold text-[#1d1d1f]">{documents.length}</span> uploaded sources
          </div>
          <div className="mt-1 text-xs">
            <span className="font-medium text-[#1d1d1f]">{completedCount}</span> ready
            {processingCount ? <span> · {processingCount} processing</span> : null}
            {failedCount ? <span> · {failedCount} failed</span> : null}
          </div>
        </div>
        <button type="button" onClick={onUploadClick} className="primary-button">
          Upload documents
        </button>
      </div>
    </header>
  );
}

export default WorkspaceHeader;
