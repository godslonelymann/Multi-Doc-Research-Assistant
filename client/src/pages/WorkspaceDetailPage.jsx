import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import EmptyState from "../components/common/EmptyState.jsx";
import ErrorState from "../components/common/ErrorState.jsx";
import Loader from "../components/common/Loader.jsx";
import ModeSwitcher from "../components/workspace/ModeSwitcher.jsx";
import PromptComposer from "../components/workspace/PromptComposer.jsx";
import ResultPanel from "../components/workspace/ResultPanel.jsx";
import SourceList from "../components/workspace/SourceList.jsx";
import UploadPanel from "../components/workspace/UploadPanel.jsx";
import WorkspaceHeader from "../components/workspace/WorkspaceHeader.jsx";
import { getErrorMessage } from "../lib/errors.js";
import { askQuestion } from "../services/chatService.js";
import { compareDocuments } from "../services/comparisonService.js";
import { deleteDocument, listDocuments, uploadDocuments } from "../services/documentService.js";
import { generateReport } from "../services/reportService.js";
import { generateSummary } from "../services/summaryService.js";
import { getWorkspace } from "../services/workspaceService.js";

const modeLabels = {
  ask: "Ask a question",
  compare: "Compare documents",
  summarize: "Generate a summary",
  report: "Generate a report",
};

const modeGuidance = {
  ask: "Ask one focused question. The answer will cite the evidence snippets it used.",
  compare: "Compare every ready document with a comprehensive, source-grounded review.",
  summarize: "Generate a high-level synthesis across all ready source material.",
  report: "Generate a structured report across the workspace. You can edit the title before creating it.",
};

function WorkspaceDetailPage({ initialMode = "ask" }) {
  const { workspaceId } = useParams();
  const [workspace, setWorkspace] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [activeMode, setActiveMode] = useState(initialMode);
  const [prompt, setPrompt] = useState("");
  const [reportTitle, setReportTitle] = useState("Research Report");
  const [results, setResults] = useState({});
  const [sessionId, setSessionId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState(false);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [deletingId, setDeletingId] = useState(null);
  const [error, setError] = useState("");

  const completedDocuments = useMemo(
    () => documents.filter((document) => document.upload_status === "completed"),
    [documents],
  );
  const failedDocuments = useMemo(
    () => documents.filter((document) => document.upload_status === "failed"),
    [documents],
  );
  const processingDocuments = useMemo(
    () => documents.filter((document) => document.upload_status === "processing"),
    [documents],
  );

  async function loadWorkspace() {
    try {
      setError("");
      setLoading(true);
      const [workspaceData, documentData] = await Promise.all([
        getWorkspace(workspaceId),
        listDocuments(workspaceId),
      ]);
      setWorkspace(workspaceData);
      setDocuments(documentData);
      setReportTitle((current) =>
        !current.trim() || current === "Research Report" ? `${workspaceData.name} Research Report` : current,
      );
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    setActiveMode(initialMode);
  }, [initialMode]);

  useEffect(() => {
    loadWorkspace();
  }, [workspaceId]);

  async function handleUpload(files) {
    try {
      setUploading(true);
      setError("");
      await uploadDocuments(workspaceId, files);
      setUploadOpen(false);
      await loadWorkspace();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setUploading(false);
    }
  }

  async function handleDelete(documentId) {
    try {
      setDeletingId(documentId);
      setError("");
      await deleteDocument(documentId);
      await loadWorkspace();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setDeletingId(null);
    }
  }

  async function handleSubmit(event) {
    event.preventDefault();
    const question = prompt.trim();
    if (activeMode === "ask" && !question) {
      return;
    }
    if (activeMode === "report" && !reportTitle.trim()) {
      return;
    }
    if (activeMode === "compare" && completedDocuments.length < 2) {
      setError("At least two ready documents are needed to compare.");
      return;
    }

    try {
      setWorking(true);
      setError("");
      if (activeMode === "ask") {
        const response = await askQuestion({
          workspace_id: Number(workspaceId),
          session_id: sessionId,
          question,
          top_k: 6,
        });
        setSessionId(response.session_id);
        setResults((current) => ({ ...current, ask: response }));
        setPrompt("");
      }

      if (activeMode === "compare") {
        const response = await compareDocuments({
          workspace_id: Number(workspaceId),
          document_ids: completedDocuments.map((document) => document.id),
          top_k_per_document: 6,
        });
        setResults((current) => ({ ...current, compare: response }));
      }

      if (activeMode === "summarize") {
        const response = await generateSummary({
          workspace_id: Number(workspaceId),
          top_k: 20,
        });
        setResults((current) => ({ ...current, summarize: response }));
      }

      if (activeMode === "report") {
        const response = await generateReport({
          workspace_id: Number(workspaceId),
          title: reportTitle.trim(),
          top_k: 30,
        });
        setResults((current) => ({ ...current, report: response }));
      }
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setWorking(false);
    }
  }

  if (loading) {
    return <Loader label="Loading workspace..." />;
  }

  if (!workspace) {
    return (
      <EmptyState
        title="Workspace not found"
        message="Go back to your workspace list and choose an available workspace."
        action={
          <Link to="/workspaces" className="secondary-button">
            Workspaces
          </Link>
        }
      />
    );
  }

  const needsSources = !documents.length;
  const hasPendingSources = documents.length > 0 && !completedDocuments.length;
  const compareNeedsMoreSources = activeMode === "compare" && completedDocuments.length < 2;
  const disabled =
    working ||
    !completedDocuments.length ||
    (activeMode === "compare" && completedDocuments.length < 2) ||
    (activeMode === "ask" && !prompt.trim()) ||
    (activeMode === "report" && !reportTitle.trim());

  return (
    <div className="space-y-8">
      <WorkspaceHeader workspace={workspace} documents={documents} onUploadClick={() => setUploadOpen(true)} />
      <ErrorState message={error} />

      <div className="grid gap-5 lg:grid-cols-[320px_minmax(0,1fr)]">
        <aside className="space-y-4">
          <section className="surface p-4">
            <div className="mb-4 flex items-center justify-between gap-4">
              <div>
                <h2 className="text-sm font-semibold text-[#1d1d1f]">Sources</h2>
                <p className="mt-1 text-sm text-[#6e6e73]">
                  {documents.length} uploaded · {completedDocuments.length} ready
                  {processingDocuments.length ? ` · ${processingDocuments.length} processing` : ""}
                  {failedDocuments.length ? ` · ${failedDocuments.length} failed` : ""}
                </p>
              </div>
              <button type="button" onClick={() => setUploadOpen(true)} className="quiet-button">
                Add
              </button>
            </div>
            <SourceList documents={documents} onDelete={handleDelete} deletingId={deletingId} />
          </section>
        </aside>

        <main className="space-y-5">
          <section className="surface p-5 sm:p-6">
            <div className="flex flex-col justify-between gap-4 xl:flex-row xl:items-center">
              <div>
                <h2 className="text-2xl font-semibold text-[#1d1d1f]">{modeLabels[activeMode]}</h2>
                <p className="mt-2 max-w-2xl text-sm leading-6 text-[#6e6e73]">{modeGuidance[activeMode]}</p>
              </div>
              <ModeSwitcher activeMode={activeMode} onChange={setActiveMode} />
            </div>
          </section>

          {needsSources ? (
            <EmptyState
              title="Upload sources to begin"
              message="Add PDFs or text files once. After processing, you can ask, compare, summarize, and generate reports from this same screen."
              action={
                <button type="button" onClick={() => setUploadOpen(true)} className="primary-button">
                  Upload documents
                </button>
              }
            />
          ) : null}

          {hasPendingSources ? (
            <EmptyState
              title="Sources are still processing"
              message="You can stay here. Once at least one source is ready, Ask, Summarize, and Report will become available."
            />
          ) : null}

          {compareNeedsMoreSources ? (
            <EmptyState
              title="Compare needs two ready sources"
              message="Upload another document or wait for processing to finish. Compare will use every ready source automatically."
            />
          ) : null}

          {!needsSources ? (
            <PromptComposer
              mode={activeMode}
              value={prompt}
              onChange={setPrompt}
              onSubmit={handleSubmit}
              loading={working}
              disabled={disabled}
              reportTitle={reportTitle}
              onReportTitleChange={setReportTitle}
            />
          ) : null}

          {working ? <Loader label="Retrieving evidence and generating a grounded result..." /> : null}
          <ResultPanel mode={activeMode} result={results[activeMode]} />
        </main>
      </div>

      <UploadPanel open={uploadOpen} onClose={() => setUploadOpen(false)} onUpload={handleUpload} loading={uploading} />
    </div>
  );
}

export default WorkspaceDetailPage;
