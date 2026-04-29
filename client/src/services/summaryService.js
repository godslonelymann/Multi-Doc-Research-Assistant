import apiClient from "./apiClient.js";

export async function generateSummary(payload) {
  const response = await apiClient.post("/summaries/generate", payload);
  return response.data;
}

export async function getSummary(summaryId) {
  const response = await apiClient.get(`/summaries/${summaryId}`);
  return response.data;
}
