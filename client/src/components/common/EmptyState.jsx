function EmptyState({ title, message, action }) {
  return (
    <div className="soft-surface p-5 sm:p-6">
      <h3 className="text-base font-semibold text-[#1d1d1f]">{title}</h3>
      {message ? <p className="mt-2 max-w-2xl text-sm leading-6 text-[#6e6e73]">{message}</p> : null}
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  );
}

export default EmptyState;
