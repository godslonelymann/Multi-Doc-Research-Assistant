const modes = [
  { id: "ask", label: "Ask" },
  { id: "compare", label: "Compare" },
  { id: "summarize", label: "Summarize" },
  { id: "report", label: "Report" },
];

function ModeSwitcher({ activeMode, onChange }) {
  return (
    <div className="inline-flex h-10 w-full rounded-lg border border-[#d2d2d7] bg-[#f5f5f7] p-1 sm:w-auto">
      {modes.map((mode) => (
        <button
          key={mode.id}
          type="button"
          onClick={() => onChange(mode.id)}
          className={[
            "flex-1 rounded-md px-3 text-sm font-medium transition sm:flex-none",
            activeMode === mode.id
              ? "bg-white text-[#1d1d1f] shadow-[0_1px_2px_rgba(0,0,0,0.08)]"
              : "text-[#6e6e73] hover:text-[#1d1d1f]",
          ].join(" ")}
        >
          {mode.label}
        </button>
      ))}
    </div>
  );
}

export default ModeSwitcher;
