import apiClient from "./apiClient.js";

export async function compareDocuments(payload) {
  const response = await apiClient.post("/compare", payload);
  return response.data;
}

export async function detectConflicts(payload) {
  const response = await apiClient.post("/conflicts", payload);
  return response.data;
}
