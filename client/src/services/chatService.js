import apiClient from "./apiClient.js";

export async function askQuestion(payload) {
  const response = await apiClient.post("/chat/ask", payload);
  return response.data;
}

export async function getChatSession(sessionId) {
  const response = await apiClient.get(`/chat/sessions/${sessionId}`);
  return response.data;
}
