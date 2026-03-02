import axios from "axios";

const api = axios.create({
  baseURL: "/api",
  timeout: 120000,
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.detail ||
      error.response?.data?.error ||
      error.message ||
      "An unexpected error occurred";
    return Promise.reject(new Error(message));
  }
);

export async function uploadFile(file) {
  const formData = new FormData();
  formData.append("file", file);
  const response = await api.post("/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
}

export async function analyzeData(fileId, question, conversationHistory = []) {
  const response = await api.post("/analyze", {
    file_id: fileId,
    question,
    conversation_history: conversationHistory,
  });
  return response.data;
}

export async function getFileMetadata(fileId) {
  const response = await api.get(`/files/${fileId}`);
  return response.data;
}

export async function deleteFile(fileId) {
  const response = await api.delete(`/files/${fileId}`);
  return response.data;
}
