import { useState } from "react";

function UploadPanel({ open, onClose, onUpload, loading }) {
  const [files, setFiles] = useState([]);

  if (!open) {
    return null;
  }

  function handleSubmit(event) {
    event.preventDefault();
    if (files.length) {
      onUpload(files);
      setFiles([]);
    }
  }

  return (
    <div className="fixed inset-0 z-20 flex items-end bg-[#1d1d1f]/25 p-4 backdrop-blur-sm sm:items-center sm:justify-center">
      <form onSubmit={handleSubmit} className="surface w-full max-w-xl p-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-2xl font-semibold text-[#1d1d1f]">Add sources</h2>
            <p className="mt-2 text-sm leading-6 text-[#6e6e73]">Upload PDFs or text files. They will be processed and added to this workspace.</p>
          </div>
          <button type="button" onClick={onClose} className="quiet-button">
            Close
          </button>
        </div>
        <label className="mt-6 block">
          <span className="label">Documents</span>
          <input
            type="file"
            multiple
            accept=".pdf,.txt,application/pdf,text/plain"
            onChange={(event) => setFiles(Array.from(event.target.files || []))}
            className="field mt-2"
          />
        </label>
        <div className="mt-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm text-[#6e6e73]">
            {files.length ? `${files.length} file${files.length === 1 ? "" : "s"} selected` : "No files selected"}
          </p>
          <button type="submit" disabled={!files.length || loading} className="primary-button">
            {loading ? "Uploading..." : "Upload"}
          </button>
        </div>
      </form>
    </div>
  );
}

export default UploadPanel;
