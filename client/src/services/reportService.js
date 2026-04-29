import apiClient from "./apiClient.js";

export async function generateReport(payload) {
  const response = await apiClient.post("/reports/generate", payload);
  return response.data;
}

export async function getReport(reportId) {
  const response = await apiClient.get(`/reports/${reportId}`);
  return response.data;
}
