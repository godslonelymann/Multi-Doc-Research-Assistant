import { Navigate, Route, Routes } from "react-router-dom";

import AppLayout from "./components/layout/AppLayout.jsx";
import NotFoundPage from "./pages/NotFoundPage.jsx";
import WorkspaceDetailPage from "./pages/WorkspaceDetailPage.jsx";
import WorkspacesPage from "./pages/WorkspacesPage.jsx";

function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<Navigate to="/workspaces" replace />} />
        <Route path="/workspaces" element={<WorkspacesPage />} />
        <Route path="/workspaces/:workspaceId" element={<WorkspaceDetailPage />} />
        <Route path="/workspaces/:workspaceId/documents" element={<WorkspaceDetailPage />} />
        <Route path="/workspaces/:workspaceId/chat" element={<WorkspaceDetailPage initialMode="ask" />} />
        <Route path="/workspaces/:workspaceId/compare" element={<WorkspaceDetailPage initialMode="compare" />} />
        <Route path="/workspaces/:workspaceId/summaries" element={<WorkspaceDetailPage initialMode="summarize" />} />
        <Route path="/workspaces/:workspaceId/reports" element={<WorkspaceDetailPage initialMode="report" />} />
        <Route path="/documents" element={<Navigate to="/workspaces" replace />} />
        <Route path="/research" element={<Navigate to="/workspaces" replace />} />
        <Route path="/compare" element={<Navigate to="/workspaces" replace />} />
        <Route path="/summaries" element={<Navigate to="/workspaces" replace />} />
        <Route path="/reports" element={<Navigate to="/workspaces" replace />} />
        <Route path="/home" element={<Navigate to="/workspaces" replace />} />
      </Route>
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}

export default App;
