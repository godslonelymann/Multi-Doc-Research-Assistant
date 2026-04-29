import apiClient from "./apiClient.js";

export async function listDocuments(workspaceId) {
  const response = await apiClient.get("/documents", {
    params: workspaceId ? { workspace_id: workspaceId } : {},
  });
  return response.data.documents;
}

export async function uploadDocuments(workspaceId, files) {
  const formData = new FormData();
  formData.append("workspace_id", workspaceId);
  files.forEach((file) => formData.append("files", file));

  const response = await apiClient.post("/documents/upload", formData);
  return response.data.documents;
}

export async function deleteDocument(documentId) {
  await apiClient.delete(`/documents/${documentId}`);
}
