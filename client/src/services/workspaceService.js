import apiClient from "./apiClient.js";

export async function listWorkspaces() {
  const response = await apiClient.get("/workspaces");
  return response.data.workspaces;
}

export async function createWorkspace(payload) {
  const response = await apiClient.post("/workspaces", payload);
  return response.data;
}

export async function getWorkspace(workspaceId) {
  const response = await apiClient.get(`/workspaces/${workspaceId}`);
  return response.data;
}
