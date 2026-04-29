import apiClient from "./apiClient.js";

export async function getHealth() {
  const response = await apiClient.get("/health");
  return response.data;
}
