import { useState, useCallback } from "react";
import { uploadFile as apiUpload, analyzeData } from "../api/client";

export default function useAnalysis() {
  const [fileId, setFileId] = useState(null);
  const [filename, setFilename] = useState(null);
  const [dataPreview, setDataPreview] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const upload = useCallback(async (file) => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await apiUpload(file);
      setFileId(data.file_id);
      setFilename(data.filename);
      setDataPreview({
        rows: data.rows,
        columns: data.columns,
        columnNames: data.column_names,
        preview: data.preview,
      });
      setMessages([]);
      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const ask = useCallback(
    async (question) => {
      if (!fileId) {
        setError("Please upload a file first.");
        return;
      }

      const userMessage = { role: "user", content: question };
      setMessages((prev) => [...prev, userMessage]);
      setIsLoading(true);
      setError(null);

      try {
        const history = messages.map((m) => ({
          role: m.role,
          content: typeof m.content === "string" ? m.content : m.content.answer || "",
        }));

        const data = await analyzeData(fileId, question, history);

        const assistantMessage = {
          role: "assistant",
          content: data,
        };
        setMessages((prev) => [...prev, assistantMessage]);
        return data;
      } catch (err) {
        setError(err.message);
        const errorMessage = {
          role: "assistant",
          content: { answer: `Error: ${err.message}`, charts: [], insights: [] },
        };
        setMessages((prev) => [...prev, errorMessage]);
      } finally {
        setIsLoading(false);
      }
    },
    [fileId, messages]
  );

  const reset = useCallback(() => {
    setFileId(null);
    setFilename(null);
    setDataPreview(null);
    setMessages([]);
    setError(null);
  }, []);

  return {
    fileId,
    filename,
    dataPreview,
    messages,
    isLoading,
    error,
    upload,
    ask,
    reset,
  };
}
