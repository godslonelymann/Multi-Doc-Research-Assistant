import { useEffect, useState } from "react";

import EmptyState from "../components/common/EmptyState.jsx";
import ErrorState from "../components/common/ErrorState.jsx";
import Loader from "../components/common/Loader.jsx";
import PageHeader from "../components/common/PageHeader.jsx";
import WorkspaceCard from "../components/workspaces/WorkspaceCard.jsx";
import { getErrorMessage } from "../lib/errors.js";
import { createWorkspace, getWorkspace, listWorkspaces } from "../services/workspaceService.js";

function WorkspacesPage() {
  const [workspaces, setWorkspaces] = useState([]);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function loadWorkspaces() {
    try {
      setError("");
      setLoading(true);
      const workspaceList = await listWorkspaces();
      const detailedWorkspaces = await Promise.all(
        workspaceList.map(async (workspace) => {
          try {
            const detail = await getWorkspace(workspace.id);
            const updatedAt = detail.documents?.reduce(
              (latest, document) =>
                !latest || new Date(document.updated_at) > new Date(latest) ? document.updated_at : latest,
              detail.created_at,
            );
            return {
              ...workspace,
              document_count: detail.documents?.length ?? 0,
              updated_at: updatedAt,
            };
          } catch {
            return workspace;
          }
        }),
      );
      setWorkspaces(detailedWorkspaces);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadWorkspaces();
  }, []);

  async function handleCreate(event) {
    event.preventDefault();
    if (!name.trim()) {
      return;
    }
    try {
      setSaving(true);
      setError("");
      await createWorkspace({ name: name.trim(), description: description.trim() || null });
      setName("");
      setDescription("");
      await loadWorkspaces();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div>
      <div className="flex flex-col justify-between gap-6 lg:flex-row lg:items-end">
        <PageHeader
          title="Workspaces"
          description="Start with a topic, add sources, then stay inside one focused workspace for every research task."
        />
      </div>
      <ErrorState message={error} />
      <form onSubmit={handleCreate} className="surface p-5 sm:p-6">
        <div className="grid gap-4 lg:grid-cols-[1fr_1fr_auto] lg:items-end">
          <label className="block">
            <span className="label">Workspace name</span>
            <input
              value={name}
              onChange={(event) => setName(event.target.value)}
              className="field mt-2"
              placeholder="Climate policy review"
            />
          </label>
          <label className="block">
            <span className="label">Short note</span>
            <input
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              className="field mt-2"
              placeholder="Papers, notes, and drafts"
            />
          </label>
          <button
            type="submit"
            disabled={saving || !name.trim()}
            className="primary-button"
          >
            {saving ? "Creating..." : "Create workspace"}
          </button>
        </div>
      </form>

      <div className="mt-8">
        {loading ? <Loader label="Loading workspaces..." /> : null}
        {!loading && !workspaces.length ? (
          <EmptyState
            title="No workspaces yet"
            message="Create one workspace for one research topic. You can upload sources and start asking questions from there."
          />
        ) : null}
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {workspaces.map((workspace) => (
            <WorkspaceCard key={workspace.id} workspace={workspace} />
          ))}
        </div>
      </div>
    </div>
  );
}

export default WorkspacesPage;
