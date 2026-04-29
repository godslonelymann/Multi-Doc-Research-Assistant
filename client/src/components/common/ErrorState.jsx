function ErrorState({ message }) {
  if (!message) {
    return null;
  }

  return (
    <div className="rounded-lg border border-[#ff3b30]/25 bg-[#fff2f1] px-4 py-3 text-sm leading-6 text-[#b42318]">
      {message}
    </div>
  );
}

export default ErrorState;
