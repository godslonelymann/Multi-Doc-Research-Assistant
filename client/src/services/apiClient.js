import axios from "axios";

const defaultBaseUrl = import.meta.env.PROD ? "/api" : "http://localhost:8000";

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || defaultBaseUrl,
});

export default apiClient;
