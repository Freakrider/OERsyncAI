import { useState } from 'react';

export default function useFileUpload() {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [progress, setProgress] = useState(0);
  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';

  async function uploadFile(file) {
    setUploading(true);
    setError(null);
    setProgress(0);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const response = await fetch(`${API_BASE_URL}/extract`, {
        method: 'POST',
        body: formData,
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      const data = await response.json();
      setProgress(100);
      return data;
    } catch (err) {
      setError('Fehler beim Upload: ' + err.message);
      setProgress(0);
      return null;
    } finally {
      setUploading(false);
    }
  }

  return { uploadFile, uploading, error, progress };
}