import apiClient from "./apiClient.js";

const DEFAULT_MAX_UPLOAD_MB = import.meta.env.PROD ? 4 : 50;
export const maxUploadSizeMb = Number(import.meta.env.VITE_MAX_UPLOAD_SIZE_MB || DEFAULT_MAX_UPLOAD_MB);
export const maxUploadSizeBytes = maxUploadSizeMb * 1024 * 1024;

export async function listDocuments(workspaceId) {
  const response = await apiClient.get("/documents", {
    params: workspaceId ? { workspace_id: workspaceId } : {},
  });
  return response.data.documents;
}

export async function uploadDocuments(workspaceId, files) {
  const totalBytes = files.reduce((sum, file) => sum + file.size, 0);
  if (totalBytes > maxUploadSizeBytes) {
    throw new Error(
      `Upload is too large for this deployment. Select files totaling ${maxUploadSizeMb} MB or less.`,
    );
  }

  const formData = new FormData();
  formData.append("workspace_id", workspaceId);
  files.forEach((file) => formData.append("files", file));

  const response = await apiClient.post("/documents/upload", formData);
  return response.data.documents;
}

export async function deleteDocument(documentId) {
  await apiClient.delete(`/documents/${documentId}`);
}
