function Loader({ label = "Loading..." }) {
  return (
    <div className="surface flex items-center gap-3 px-4 py-3 text-sm text-[#6e6e73]">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-[#d2d2d7] border-t-[#0071e3]" />
      <span>{label}</span>
    </div>
  );
}

export default Loader;
