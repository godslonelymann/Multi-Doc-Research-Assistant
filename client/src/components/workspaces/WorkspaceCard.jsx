import { Link } from "react-router-dom";

function WorkspaceCard({ workspace }) {
  const documentCount = workspace.document_count ?? workspace.documents?.length ?? 0;
  const updatedAt = workspace.updated_at || workspace.created_at;
  const updatedLabel = updatedAt
    ? new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric", year: "numeric" }).format(new Date(updatedAt))
    : "Recently";

  return (
    <article className="surface p-5 transition hover:border-[#b9b9bf] hover:shadow-[0_6px_18px_rgba(0,0,0,0.06)]">
      <div className="flex min-h-40 flex-col">
        <p className="text-xs font-medium uppercase text-[#86868b]">{documentCount} documents</p>
        <h3 className="mt-4 line-clamp-2 text-2xl font-semibold text-[#1d1d1f]">{workspace.name}</h3>
        <p className="mt-3 line-clamp-3 flex-1 text-sm leading-6 text-[#6e6e73]">
          {workspace.description || "A quiet place for sources, questions, comparisons, summaries, and reports."}
        </p>
        <div className="mt-6 flex items-center justify-between gap-4">
          <p className="text-sm text-[#86868b]">Updated {updatedLabel}</p>
          <Link
            to={`/workspaces/${workspace.id}`}
            className="secondary-button shrink-0"
          >
            Open
          </Link>
        </div>
      </div>
    </article>
  );
}

export default WorkspaceCard;
