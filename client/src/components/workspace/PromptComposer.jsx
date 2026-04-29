const modeCopy = {
  ask: {
    label: "Question",
    placeholder: "What do the sources say about the methodology?",
    button: "Ask",
  },
  compare: {
    button: "Compare all ready documents",
  },
  summarize: {
    button: "Generate summary",
  },
  report: {
    button: "Generate report",
  },
};

function PromptComposer({
  mode,
  value,
  onChange,
  onSubmit,
  loading,
  disabled,
  reportTitle,
  onReportTitleChange,
}) {
  const copy = modeCopy[mode] || modeCopy.ask;

  return (
    <form onSubmit={onSubmit} className="surface p-5 sm:p-6">
      <div className="space-y-4">
        {mode === "report" ? (
          <label className="block">
            <span className="label">Report title</span>
            <input
              value={reportTitle}
              onChange={(event) => onReportTitleChange(event.target.value)}
              className="field mt-2"
              placeholder="Research Report"
            />
          </label>
        ) : null}
        {mode === "ask" ? (
          <label className="block">
            <span className="label">{copy.label}</span>
            <textarea
              rows="4"
              value={value}
              onChange={(event) => onChange(event.target.value)}
              className="field mt-2 resize-none"
              placeholder={copy.placeholder}
            />
          </label>
        ) : null}
      </div>
      <div className="mt-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-sm text-[#6e6e73]">
          {mode === "ask"
            ? "Answers use retrieved evidence snippets."
            : "This will use all ready sources without extra instructions."}
        </p>
        <button type="submit" disabled={loading || disabled} className="primary-button">
          {loading ? "Working..." : copy.button}
        </button>
      </div>
    </form>
  );
}

export default PromptComposer;
