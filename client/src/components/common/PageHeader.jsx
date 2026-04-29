function PageHeader({ title, description }) {
  return (
    <div className="mb-6">
      <h2 className="text-3xl font-semibold text-[#1d1d1f]">{title}</h2>
      {description ? <p className="mt-2 max-w-2xl text-sm leading-6 text-[#6e6e73]">{description}</p> : null}
    </div>
  );
}

export default PageHeader;
